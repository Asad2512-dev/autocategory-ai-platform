<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class PredictionLog extends Model
{
    use HasFactory;

    protected $fillable = [
        'product_id',
        'input_title',
        'input_description',
        'predicted_category_name',
        'confidence',
        'low_confidence',
        'review_needed',
        'flagged_for_retraining',
        'prediction_source',
        'message',
        'top_candidates',
        'suggested_new_category',
        'final_category_name',
        'corrected_by_admin',
        'auto_approved',
        'feedback_exported',
        'feedback_export_failed',
        'feedback_exported_at',
        'feedback_export_error',
    ];

    protected $casts = [
        'confidence' => 'float',
        'low_confidence' => 'boolean',
        'review_needed' => 'boolean',
        'flagged_for_retraining' => 'boolean',
        'top_candidates' => 'array',
        'corrected_by_admin' => 'boolean',
        'auto_approved' => 'boolean',
        'feedback_exported' => 'boolean',
        'feedback_export_failed' => 'boolean',
        'feedback_exported_at' => 'datetime',
    ];

    public function product(): BelongsTo
    {
        return $this->belongsTo(Product::class);
    }
}
