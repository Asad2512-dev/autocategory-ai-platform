<?php

namespace App\Services;

use App\Jobs\PredictProductCategoryJob;
use Carbon\Carbon;
use App\Models\Category;
use App\Models\PredictionLog;
use App\Models\Product;
use App\Models\User;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;

class ProductService
{
    public function __construct(private readonly PredictionService $predictionService)
    {
    }

    public function createForUser(User $user, array $data): Product
    {
        $product = new Product();
        $product->fill($data);
        $product->user_id = $user->id;
        $product->slug = $this->generateUniqueSlug($data['title']);
        $product->status = $data['status'] ?? 'active';
        $product->save();

        return $this->freshProduct($product);
    }

    public function triggerPrediction(Product $product, string $mode = 'sync'): Product
    {
        if ($mode === 'async') {
            PredictProductCategoryJob::dispatch($product->id);

            return $this->freshProduct($product);
        }

        return $this->predictAndPersist($product);
    }

    public function predictAndPersist(Product $product): Product
    {
        $result = $this->predictionService->predict($product->title, $product->description);

        if (! $result) {
            throw new \RuntimeException('Prediction service unavailable. Please try again later.');
        }

        return $this->autoFinalizePredictionFromMlResult($product, $result);
    }

    /**
     * Persist ML/FastAPI result: set predicted + final category on the product, log history, auto-approve.
     *
     * @param  array<string, mixed>  $result
     */
    public function autoFinalizePredictionFromMlResult(Product $product, array $result): Product
    {
        $predictedCategoryName = trim((string) $result['predicted_category']);
        $confidence = (float) $result['confidence'];
        $lowConfidence = (bool) ($result['low_confidence'] ?? false);
        $reviewNeeded = (bool) ($result['review_needed'] ?? false);
        $flaggedForRetraining = (bool) ($result['flagged_for_retraining'] ?? false);
        $predictionSource = isset($result['prediction_source']) ? (string) $result['prediction_source'] : null;
        $message = isset($result['message']) ? (string) $result['message'] : null;
        $topCandidates = is_array($result['top_candidates'] ?? null) ? $result['top_candidates'] : null;
        $suggestedNew = isset($result['suggested_new_category']) && is_string($result['suggested_new_category'])
            ? trim($result['suggested_new_category'])
            : null;
        if ($suggestedNew === '') {
            $suggestedNew = null;
        }

        $category = Category::query()
            ->whereRaw('LOWER(name) = ?', [Str::lower($predictedCategoryName)])
            ->first();

        if (! $category) {
            throw new \RuntimeException(
                'Prediction returned unknown category "'.$predictedCategoryName.'". Add it to categories or retrain the model.'
            );
        }

        $product->predicted_category_id = $category->id;
        $product->final_category_id = $category->id;
        $product->ai_confidence = $confidence;
        $product->is_ai_classified = true;
        $product->admin_reviewed = true;
        $product->save();

        PredictionLog::query()->create([
            'product_id' => $product->id,
            'input_title' => $product->title,
            'input_description' => $product->description,
            'predicted_category_name' => $predictedCategoryName,
            'confidence' => $confidence,
            'low_confidence' => $lowConfidence,
            'review_needed' => $reviewNeeded,
            'flagged_for_retraining' => $flaggedForRetraining,
            'prediction_source' => $predictionSource,
            'message' => $message,
            'top_candidates' => $topCandidates,
            'suggested_new_category' => $suggestedNew,
            'final_category_name' => $category->name,
            'corrected_by_admin' => false,
            'auto_approved' => true,
        ]);

        return $this->freshProduct($product, withLatestPredictionLog: true);
    }

    public function updateProduct(Product $product, array $data): Product
    {
        if (array_key_exists('title', $data) && $data['title'] !== $product->title) {
            $data['slug'] = $this->generateUniqueSlug($data['title'], $product->id);
        }

        $product->fill($data);
        $product->save();

        return $this->freshProduct($product);
    }

    public function approvePrediction(Product $product): Product
    {
        if (! $product->predicted_category_id) {
            throw new \RuntimeException('Cannot approve because predicted category is missing.');
        }

        $product->final_category_id = $product->predicted_category_id;
        $product->admin_reviewed = true;
        $product->save();

        $latestLog = $product->predictionLogs()->latest('id')->first();

        if ($latestLog) {
            $latestLog->final_category_name = $product->predictedCategory?->name;
            $latestLog->corrected_by_admin = false;
            $latestLog->save();
        }

        return $this->freshProduct($product, withLatestPredictionLog: true);
    }

    public function correctPrediction(Product $product, Category $finalCategory): Product
    {
        $predictionChanged = $product->predicted_category_id !== $finalCategory->id;

        $product->final_category_id = $finalCategory->id;
        $product->admin_reviewed = true;
        $product->save();

        $latestLog = $product->predictionLogs()->latest('id')->first();

        if ($latestLog) {
            $latestLog->final_category_name = $finalCategory->name;
            $latestLog->corrected_by_admin = $predictionChanged;
            $latestLog->save();

            if ($predictionChanged) {
                $this->retryFeedbackExportForLog($latestLog);
            }
        }

        return $this->freshProduct($product, withLatestPredictionLog: true);
    }

    private function freshProduct(Product $product, bool $withLatestPredictionLog = false): Product
    {
        $with = ['predictedCategory', 'finalCategory'];
        if ($withLatestPredictionLog) {
            $with[] = 'latestPredictionLog';
        }

        return $product->fresh($with);
    }

    private function generateUniqueSlug(string $title, ?int $ignoreId = null): string
    {
        $base = Str::slug($title);
        $slug = $base;
        $counter = 1;

        while ($this->slugExists($slug, $ignoreId)) {
            $slug = $base.'-'.$counter;
            $counter++;
        }

        return $slug;
    }

    private function slugExists(string $slug, ?int $ignoreId = null): bool
    {
        $query = Product::query()->where('slug', $slug);

        if ($ignoreId) {
            $query->where('id', '!=', $ignoreId);
        }

        return $query->exists();
    }

    public function retryFeedbackExportForLog(PredictionLog $log): PredictionLog
    {
        $log->loadMissing('product');
        $categoryName = trim((string) $log->final_category_name);

        if (! $log->corrected_by_admin || $categoryName === '') {
            throw new \RuntimeException('Feedback export is only available for corrected predictions.');
        }

        $feedbackPayload = $this->buildFeedbackPayloadFromLog($log);
        $result = $this->predictionService->sendFeedback($feedbackPayload);

        if ($result['success']) {
            $log->feedback_exported = true;
            $log->feedback_export_failed = false;
            $log->feedback_exported_at = Carbon::now();
            $log->feedback_export_error = null;
            $log->save();

            return $log->fresh();
        }

        $error = trim((string) ($result['error'] ?? 'Feedback export failed.'));
        $log->feedback_exported = false;
        $log->feedback_export_failed = true;
        $log->feedback_export_error = Str::limit($error, 2000, '');
        $log->save();

        Log::warning('Feedback export failed for corrected prediction log.', [
            'prediction_log_id' => $log->id,
            'product_id' => $log->product_id,
            'error' => $error,
        ]);

        return $log->fresh();
    }

    public function retryFailedFeedbackExports(): int
    {
        $logs = PredictionLog::query()
            ->where('corrected_by_admin', true)
            ->where('feedback_export_failed', true)
            ->orderBy('id')
            ->get();

        $successCount = 0;

        foreach ($logs as $log) {
            $updated = $this->retryFeedbackExportForLog($log);
            if ($updated->feedback_exported) {
                $successCount++;
            }
        }

        return $successCount;
    }

    /**
     * @return array<string, bool|float|string>
     */
    private function buildFeedbackPayloadFromLog(PredictionLog $log): array
    {
        $product = $log->product;

        if (! $product) {
            throw new \RuntimeException('Feedback export failed because the product record is missing.');
        }

        return [
            'title' => $product->title,
            'description' => $product->description,
            'predicted_category' => $log->predicted_category_name,
            'corrected_category' => (string) $log->final_category_name,
            'confidence' => (float) $log->confidence,
            'low_confidence' => (bool) $log->low_confidence,
            'review_needed' => (bool) $log->review_needed,
            'flagged_for_retraining' => (bool) $log->flagged_for_retraining,
            'prediction_source' => (string) ($log->prediction_source ?? 'model'),
        ];
    }
}
