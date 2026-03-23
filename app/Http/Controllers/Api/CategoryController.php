<?php

namespace App\Http\Controllers\Api;

use App\Http\Resources\CategoryResource;
use App\Models\Category;
use Illuminate\Http\JsonResponse;

class CategoryController extends ApiController
{
    public function index(): JsonResponse
    {
        $categories = Category::query()->where('status', 'active')->orderBy('name')->get();

        return $this->successResponse(
            'Categories fetched successfully.',
            CategoryResource::collection($categories)->resolve()
        );
    }
}
