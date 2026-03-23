@extends('admin.layouts.app')

@section('content')
<div class="d-flex justify-content-between align-items-center mb-3">
    <h3 class="mb-0">Admin Dashboard</h3>
</div>

<div class="row g-3">
    <div class="col-md-6 col-lg-3">
        <div class="card shadow-sm">
            <div class="card-body">
                <h6>Total Users</h6>
                <h3 class="mb-0">{{ $stats['total_users'] }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-6 col-lg-3">
        <div class="card shadow-sm">
            <div class="card-body">
                <h6>Total Products</h6>
                <h3 class="mb-0">{{ $stats['total_products'] }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-6 col-lg-3">
        <div class="card shadow-sm">
            <div class="card-body">
                <h6>Total Categories</h6>
                <h3 class="mb-0">{{ $stats['total_categories'] }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-6 col-lg-3">
        <div class="card shadow-sm border-info">
            <div class="card-body">
                <h6>Total AI-Classified</h6>
                <h3 class="mb-0">{{ $stats['total_ai_classified'] }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-6 col-lg-4">
        <div class="card shadow-sm border-success">
            <div class="card-body">
                <h6>Reviewed Predictions</h6>
                <h3 class="mb-0">{{ $stats['reviewed_predictions'] }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-6 col-lg-4">
        <div class="card shadow-sm border-warning">
            <div class="card-body">
                <h6>Corrected Predictions</h6>
                <h3 class="mb-0">{{ $stats['corrected_predictions'] }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-12 col-lg-4">
        <div class="card shadow-sm border-primary">
            <div class="card-body">
                <h6>Average Confidence Score</h6>
                <h3 class="mb-0">{{ number_format($stats['average_confidence_score'], 4) }}</h3>
            </div>
        </div>
    </div>
</div>

<div class="row g-3 mt-1">
    <div class="col-lg-6">
        <div class="card shadow-sm h-100">
            <div class="card-header bg-white">
                <strong>Latest Products</strong>
            </div>
            <div class="table-responsive">
                <table class="table table-sm mb-0">
                    <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>User</th>
                        <th>Status</th>
                    </tr>
                    </thead>
                    <tbody>
                    @forelse($latestProducts as $product)
                        <tr>
                            <td>{{ $product->id }}</td>
                            <td>{{ $product->title }}</td>
                            <td>{{ $product->user?->name ?? '-' }}</td>
                            <td>{{ $product->status }}</td>
                        </tr>
                    @empty
                        <tr><td colspan="4" class="text-center py-3">No products yet.</td></tr>
                    @endforelse
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="col-lg-6">
        <div class="card shadow-sm h-100">
            <div class="card-header bg-white">
                <strong>Latest Predictions</strong>
            </div>
            <div class="table-responsive">
                <table class="table table-sm mb-0">
                    <thead>
                    <tr>
                        <th>ID</th>
                        <th>Product</th>
                        <th>Predicted</th>
                        <th>Confidence</th>
                    </tr>
                    </thead>
                    <tbody>
                    @forelse($latestPredictions as $prediction)
                        <tr>
                            <td>{{ $prediction->id }}</td>
                            <td>{{ $prediction->product?->title ?? '-' }}</td>
                            <td>{{ $prediction->predicted_category_name }}</td>
                            <td>{{ number_format($prediction->confidence, 4) }}</td>
                        </tr>
                    @empty
                        <tr><td colspan="4" class="text-center py-3">No predictions yet.</td></tr>
                    @endforelse
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
@endsection
