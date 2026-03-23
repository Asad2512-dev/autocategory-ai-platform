<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class PredictionLogResource extends JsonResource
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
            'product_id' => $this->product_id,
            'input_title' => $this->input_title,
            'input_description' => $this->input_description,
            'predicted_category_name' => $this->predicted_category_name,
            'confidence' => $this->confidence,
            'low_confidence' => $this->low_confidence,
            'review_needed' => $this->review_needed,
            'flagged_for_retraining' => $this->flagged_for_retraining,
            'prediction_source' => $this->prediction_source,
            'message' => $this->message,
            'top_candidates' => $this->top_candidates,
            'suggested_new_category' => $this->suggested_new_category,
            'final_category_name' => $this->final_category_name,
            'corrected_by_admin' => $this->corrected_by_admin,
            'auto_approved' => (bool) $this->auto_approved,
            'feedback_exported' => $this->feedback_exported,
            'feedback_export_failed' => $this->feedback_export_failed,
            'feedback_exported_at' => $this->feedback_exported_at,
            'feedback_export_error' => $this->feedback_export_error,
            'created_at' => $this->created_at,
        ];
    }
}
