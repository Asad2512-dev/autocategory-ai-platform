<?php

namespace App\Http\Controllers\Api;

use App\Http\Requests\Product\IndexProductRequest;
use App\Http\Requests\Product\StoreProductRequest;
use App\Http\Requests\Product\UpdateProductRequest;
use App\Http\Resources\ProductResource;
use App\Models\Product;
use App\Services\ProductService;
use Illuminate\Http\Exceptions\HttpResponseException;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ProductController extends ApiController
{
    public function __construct(private readonly ProductService $productService)
    {
    }

    public function index(IndexProductRequest $request): JsonResponse
    {
        $validated = $request->validated();

        $query = Product::query()
            ->with(['predictedCategory', 'finalCategory', 'latestPredictionLog'])
            ->where('user_id', $request->user()->id);

        if (isset($validated['category_id'])) {
            $categoryId = (int) $validated['category_id'];
            $query->where(function ($builder) use ($categoryId) {
                $builder->where('predicted_category_id', $categoryId)
                    ->orWhere('final_category_id', $categoryId);
            });
        }

        if (! empty($validated['search'])) {
            $search = trim((string) $validated['search']);

            if ($search !== '') {
                $query->where('title', 'like', "%{$search}%");
            }
        }

        $products = $query->latest('id')->paginate(10)->withQueryString();

        return $this->successResponse(
            'Products fetched successfully.',
            $this->paginatedData($products, ProductResource::collection($products)->resolve())
        );
    }

    public function store(StoreProductRequest $request): JsonResponse
    {
        $validated = $request->validated();
        $triggerPrediction = (bool) ($validated['trigger_prediction'] ?? false);
        $predictionMode = (string) ($validated['prediction_mode'] ?? 'sync');

        unset($validated['trigger_prediction'], $validated['prediction_mode']);

        $product = $this->productService->createForUser($request->user(), $validated);

        $prediction = [
            'triggered' => false,
            'mode' => null,
            'status' => 'not_requested',
        ];

        if ($triggerPrediction) {
            try {
                $product = $this->productService->triggerPrediction($product, $predictionMode);

                $prediction = [
                    'triggered' => true,
                    'mode' => $predictionMode,
                    'status' => $predictionMode === 'async' ? 'queued' : 'completed',
                ];

                if ($predictionMode === 'sync' && $prediction['status'] === 'completed') {
                    $prediction['auto_approved'] = true;
                    $prediction['predicted_category'] = $product->predictedCategory?->name;
                    $prediction['final_category'] = $product->finalCategory?->name;
                    $prediction['ai_confidence'] = $product->ai_confidence;
                    $prediction['prediction_source'] = $product->latestPredictionLog?->prediction_source;
                }
            } catch (\RuntimeException $exception) {
                $prediction = [
                    'triggered' => true,
                    'mode' => $predictionMode,
                    'status' => 'failed',
                    'error' => $exception->getMessage(),
                ];
            }
        }

        return $this->successResponse('Product created successfully.', [
            'product' => new ProductResource($product),
            'prediction' => $prediction,
        ], 201);
    }

    public function show(Request $request, Product $product): JsonResponse
    {
        $this->ensureOwnership($request, $product);

        return $this->successResponse(
            'Product fetched successfully.',
            new ProductResource($product->load(['predictedCategory', 'finalCategory', 'latestPredictionLog']))
        );
    }

    public function update(UpdateProductRequest $request, Product $product): JsonResponse
    {
        $this->ensureOwnership($request, $product);

        $updated = $this->productService->updateProduct($product, $request->validated());

        return $this->successResponse('Product updated successfully.', new ProductResource($updated));
    }

    public function destroy(Request $request, Product $product): JsonResponse
    {
        $this->ensureOwnership($request, $product);
        $product->delete();

        return $this->successResponse('Product deleted successfully.');
    }

    public function predict(Request $request, Product $product): JsonResponse
    {
        $this->ensureOwnership($request, $product);

        try {
            $predicted = $this->productService->predictAndPersist($product);

            return $this->successResponse('Prediction generated and auto-approved successfully.', [
                'product' => new ProductResource($predicted),
                'auto_approved' => true,
                'predicted_category' => $predicted->predictedCategory?->name,
                'final_category' => $predicted->finalCategory?->name,
                'ai_confidence' => $predicted->ai_confidence,
                'prediction_source' => $predicted->latestPredictionLog?->prediction_source,
            ]);
        } catch (\RuntimeException $exception) {
            return $this->errorResponse($exception->getMessage(), null, 503);
        }
    }

    private function ensureOwnership(Request $request, Product $product): void
    {
        $user = $request->user();

        if (! $user || ($user->id !== $product->user_id && ! $user->isAdmin())) {
            throw new HttpResponseException(
                $this->forbiddenResponse('You are not allowed to access this product.')
            );
        }
    }
}
