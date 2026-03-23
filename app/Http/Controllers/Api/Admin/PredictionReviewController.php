<?php

namespace App\Http\Controllers\Api\Admin;

use App\Http\Requests\Admin\ApprovePredictionRequest;
use App\Http\Requests\Admin\CorrectPredictionRequest;
use App\Http\Resources\PredictionLogResource;
use App\Http\Resources\ProductResource;
use App\Models\Category;
use App\Models\PredictionLog;
use App\Models\Product;
use App\Services\ProductService;
use App\Http\Controllers\Api\ApiController;
use Illuminate\Http\JsonResponse;

class PredictionReviewController extends ApiController
{
    public function __construct(private readonly ProductService $productService)
    {
    }

    public function index(): JsonResponse
    {
        $products = Product::query()
            ->with(['user', 'predictedCategory', 'finalCategory', 'latestPredictionLog'])
            ->where('is_ai_classified', true)
            ->latest('id')
            ->paginate(10);

        return $this->successResponse(
            'Predictions fetched successfully.',
            $this->paginatedData($products, ProductResource::collection($products)->resolve())
        );
    }

    public function approve(ApprovePredictionRequest $request, Product $product): JsonResponse
    {
        try {
            $reviewed = $this->productService->approvePrediction($product);

            return $this->successResponse('Prediction approved successfully.', new ProductResource($reviewed));
        } catch (\RuntimeException $exception) {
            return $this->errorResponse($exception->getMessage(), null, 422);
        }
    }

    public function correct(CorrectPredictionRequest $request, Product $product): JsonResponse
    {
        $category = Category::query()->findOrFail((int) $request->validated('final_category_id'));
        $reviewed = $this->productService->correctPrediction($product, $category);

        return $this->successResponse('Prediction corrected successfully.', new ProductResource($reviewed));
    }

    public function retryFeedbackExport(PredictionLog $predictionLog): JsonResponse
    {
        try {
            $updatedLog = $this->productService->retryFeedbackExportForLog($predictionLog);

            if ($updatedLog->feedback_exported) {
                return $this->successResponse(
                    'Feedback export retried successfully.',
                    new PredictionLogResource($updatedLog)
                );
            }

            return $this->errorResponse(
                'Feedback export retry failed.',
                new PredictionLogResource($updatedLog),
                422
            );
        } catch (\RuntimeException $exception) {
            return $this->errorResponse($exception->getMessage(), null, 422);
        }
    }

    public function retryFailedFeedbackExports(): JsonResponse
    {
        $successCount = $this->productService->retryFailedFeedbackExports();

        return $this->successResponse('Failed feedback exports retried.', [
            'retried_successfully' => $successCount,
        ]);
    }
}
