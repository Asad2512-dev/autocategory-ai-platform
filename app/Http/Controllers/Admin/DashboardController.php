<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Category;
use App\Models\PredictionLog;
use App\Models\Product;
use App\Models\User;
use Illuminate\View\View;

class DashboardController extends Controller
{
    public function index(): View
    {
        $productStats = Product::query()
            ->selectRaw('COUNT(*) as total_products')
            ->selectRaw('SUM(CASE WHEN is_ai_classified = 1 THEN 1 ELSE 0 END) as total_ai_classified')
            ->selectRaw('SUM(CASE WHEN admin_reviewed = 1 THEN 1 ELSE 0 END) as reviewed_predictions')
            ->selectRaw('AVG(ai_confidence) as average_confidence_score')
            ->first();

        $stats = [
            'total_users' => User::query()->count(),
            'total_products' => (int) ($productStats->total_products ?? 0),
            'total_categories' => Category::query()->count(),
            'total_ai_classified' => (int) ($productStats->total_ai_classified ?? 0),
            'reviewed_predictions' => (int) ($productStats->reviewed_predictions ?? 0),
            'corrected_predictions' => PredictionLog::query()->where('corrected_by_admin', true)->count(),
            'average_confidence_score' => round((float) ($productStats->average_confidence_score ?? 0), 4),
        ];

        $latestProducts = Product::query()
            ->with(['user', 'predictedCategory', 'finalCategory'])
            ->latest('id')
            ->limit(8)
            ->get();

        $latestPredictions = PredictionLog::query()
            ->with('product')
            ->latest('id')
            ->limit(8)
            ->get();

        return view('admin.dashboard', compact('stats', 'latestProducts', 'latestPredictions'));
    }
}
