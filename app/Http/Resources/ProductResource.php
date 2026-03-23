<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class ProductResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     *
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'user_id' => $this->user_id,
            'title' => $this->title,
            'slug' => $this->slug,
            'description' => $this->description,
            'brand' => $this->brand,
            'sku' => $this->sku,
            'price' => $this->price,
            'stock' => $this->stock,
            'image' => $this->image,
            'predicted_category_id' => $this->predicted_category_id,
            'final_category_id' => $this->final_category_id,
            'predicted_category' => $this->predictedCategory?->name,
            'final_category' => $this->finalCategory?->name,
            'ai_confidence' => $this->ai_confidence,
            'is_ai_classified' => $this->is_ai_classified,
            'admin_reviewed' => $this->admin_reviewed,
            'prediction_source' => $this->whenLoaded('latestPredictionLog', fn () => $this->latestPredictionLog?->prediction_source),
            'suggested_new_category' => $this->whenLoaded('latestPredictionLog', fn () => $this->latestPredictionLog?->suggested_new_category),
            'auto_approved' => $this->whenLoaded('latestPredictionLog', fn () => (bool) $this->latestPredictionLog?->auto_approved),
            'latest_prediction_log' => $this->whenLoaded('latestPredictionLog', function () {
                return [
                    'id' => $this->latestPredictionLog?->id,
                    'prediction_source' => $this->latestPredictionLog?->prediction_source,
                    'suggested_new_category' => $this->latestPredictionLog?->suggested_new_category,
                    'auto_approved' => (bool) $this->latestPredictionLog?->auto_approved,
                    'low_confidence' => $this->latestPredictionLog?->low_confidence,
                    'review_needed' => $this->latestPredictionLog?->review_needed,
                    'corrected_by_admin' => $this->latestPredictionLog?->corrected_by_admin,
                    'feedback_exported' => $this->latestPredictionLog?->feedback_exported,
                    'feedback_export_failed' => $this->latestPredictionLog?->feedback_export_failed,
                    'feedback_exported_at' => $this->latestPredictionLog?->feedback_exported_at,
                    'feedback_export_error' => $this->latestPredictionLog?->feedback_export_error,
                ];
            }),
            'status' => $this->status,
            'created_at' => $this->created_at,
            'updated_at' => $this->updated_at,
        ];
    }
}
