@extends('admin.layouts.app')

@section('content')
<h3 class="mb-3">Products</h3>

<div class="card shadow-sm">
    <div class="table-responsive">
        <table class="table table-striped mb-0">
            <thead>
            <tr>
                <th>ID</th>
                <th>User</th>
                <th>Title</th>
                <th>Predicted</th>
                <th>Final</th>
                <th>Confidence</th>
                <th>Details</th>
            </tr>
            </thead>
            <tbody>
            @forelse($products as $product)
                <tr>
                    <td>{{ $product->id }}</td>
                    <td>{{ $product->user?->name }}</td>
                    <td>{{ $product->title }}</td>
                    <td>{{ $product->predictedCategory?->name ?? '-' }}</td>
                    <td>{{ $product->finalCategory?->name ?? '-' }}</td>
                    <td>{{ $product->ai_confidence ? number_format($product->ai_confidence, 2) : '-' }}</td>
                    <td><a class="btn btn-sm btn-outline-primary" href="{{ route('admin.products.show', $product) }}">View</a></td>
                </tr>
            @empty
                <tr><td colspan="7" class="text-center py-4">No products found.</td></tr>
            @endforelse
            </tbody>
        </table>
    </div>
</div>

<div class="mt-3">{{ $products->links() }}</div>
@endsection
