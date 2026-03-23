<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Product;
use Illuminate\View\View;

class ProductController extends Controller
{
    public function index(): View
    {
        $products = Product::query()
            ->with(['user', 'predictedCategory', 'finalCategory'])
            ->latest('id')
            ->paginate(12);

        return view('admin.products.index', compact('products'));
    }

    public function show(Product $product): View
    {
        $product->load(['user', 'predictedCategory', 'finalCategory']);

        return view('admin.products.show', compact('product'));
    }
}
