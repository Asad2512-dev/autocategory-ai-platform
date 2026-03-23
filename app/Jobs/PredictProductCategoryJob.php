<?php

namespace App\Jobs;

use App\Models\Product;
use App\Services\ProductService;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Foundation\Queue\InteractsWithQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;

class PredictProductCategoryJob implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;

    public int $backoff = 10;

    public function __construct(private readonly int $productId)
    {
        $this->onQueue('predictions');
    }

    /**
     * Execute the job.
     */
    public function handle(ProductService $productService): void
    {
        $product = Product::query()->find($this->productId);

        if (! $product) {
            return;
        }

        try {
            $productService->predictAndPersist($product);
        } catch (\Throwable $exception) {
            Log::warning('Queued prediction failed.', [
                'product_id' => $this->productId,
                'message' => $exception->getMessage(),
            ]);

            throw $exception;
        }
    }
}
