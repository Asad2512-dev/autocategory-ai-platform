<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class PredictionService
{
    /**
    * @return array{
    *   predicted_category: string,
    *   suggested_new_category: string|null,
    *   confidence: float,
    *   low_confidence: bool,
    *   review_needed: bool,
    *   flagged_for_retraining: bool,
    *   prediction_source: string|null,
    *   message: string|null,
    *   top_candidates: array<int, array<string, mixed>>|null
    * }|null
     */
    public function predict(string $title, string $description): ?array
    {
        $baseUrl = rtrim((string) config('services.ml_service.base_url'), '/');

        if ($baseUrl === '') {
            Log::error('Prediction service base URL is not configured.');

            return null;
        }

        try {
            $response = Http::timeout(10)->post($baseUrl.'/predict', [
                'title' => $title,
                'description' => $description,
            ]);

            if (! $response->successful()) {
                Log::warning('Prediction service returned a non-success status.', [
                    'status' => $response->status(),
                    'body' => $response->body(),
                ]);

                return null;
            }

            $payload = $response->json();

            if (! is_array($payload)) {
                return null;
            }

            if (! isset($payload['predicted_category'], $payload['confidence'])) {
                return null;
            }

            $suggested = $payload['suggested_new_category'] ?? null;
            if (is_string($suggested)) {
                $suggested = trim($suggested) !== '' ? trim($suggested) : null;
            } else {
                $suggested = null;
            }

            return [
                'predicted_category' => (string) $payload['predicted_category'],
                'suggested_new_category' => $suggested,
                'confidence' => (float) $payload['confidence'],
                'low_confidence' => (bool) ($payload['low_confidence'] ?? false),
                'review_needed' => (bool) ($payload['review_needed'] ?? false),
                'flagged_for_retraining' => (bool) ($payload['flagged_for_retraining'] ?? false),
                'prediction_source' => isset($payload['prediction_source']) ? (string) $payload['prediction_source'] : null,
                'message' => isset($payload['message']) ? (string) $payload['message'] : null,
                'top_candidates' => is_array($payload['top_candidates'] ?? null) ? $payload['top_candidates'] : null,
            ];
        } catch (\Throwable $exception) {
            Log::error('Prediction service connection failed.', [
                'message' => $exception->getMessage(),
            ]);

            return null;
        }
    }

    /**
     * @return array{success: bool, error: string|null}
     */
    public function sendFeedback(array $payload): array
    {
        $baseUrl = rtrim((string) config('services.ml_service.base_url'), '/');

        if ($baseUrl === '') {
            $error = 'Prediction service base URL is not configured for feedback export.';
            Log::error($error);

            return ['success' => false, 'error' => $error];
        }

        try {
            $response = Http::timeout(10)->post($baseUrl.'/feedback', $payload);

            if (! $response->successful()) {
                $error = 'Feedback export failed with status '.$response->status();
                Log::warning('Feedback export failed with non-success status.', [
                    'status' => $response->status(),
                    'body' => $response->body(),
                ]);

                return ['success' => false, 'error' => $error];
            }

            return ['success' => true, 'error' => null];
        } catch (\Throwable $exception) {
            $error = $exception->getMessage();
            Log::error('Feedback export connection failed.', [
                'message' => $error,
            ]);

            return ['success' => false, 'error' => $error];
        }
    }
}
