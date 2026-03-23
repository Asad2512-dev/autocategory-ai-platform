<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasOne;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Product extends Model
{
    use HasFactory;

    protected $fillable = [
        'user_id',
        'title',
        'slug',
        'description',
        'brand',
        'sku',
        'price',
        'stock',
        'image',
        'predicted_category_id',
        'final_category_id',
        'ai_confidence',
        'is_ai_classified',
        'admin_reviewed',
        'status',
    ];

    protected $casts = [
        'price' => 'decimal:2',
        'stock' => 'integer',
        'ai_confidence' => 'float',
        'is_ai_classified' => 'boolean',
        'admin_reviewed' => 'boolean',
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function predictedCategory(): BelongsTo
    {
        return $this->belongsTo(Category::class, 'predicted_category_id');
    }

    public function finalCategory(): BelongsTo
    {
        return $this->belongsTo(Category::class, 'final_category_id');
    }

    public function predictionLogs(): HasMany
    {
        return $this->hasMany(PredictionLog::class);
    }

    public function latestPredictionLog(): HasOne
    {
        return $this->hasOne(PredictionLog::class)->latestOfMany();
    }
}
