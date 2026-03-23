<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Product;
use Illuminate\View\View;

class PredictionController extends Controller
{
    public function index(): View
    {
        $products = Product::query()
            ->with(['user', 'predictedCategory', 'finalCategory', 'latestPredictionLog'])
            ->where('is_ai_classified', true)
            ->latest('id')
            ->paginate(12);

        return view('admin.predictions.index', compact('products'));
    }
}
