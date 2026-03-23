@extends('admin.layouts.app')

@section('content')
<h3 class="mb-3">Product Detail</h3>

<div class="card shadow-sm mb-3">
    <div class="card-body">
        <h5>{{ $product->title }}</h5>
        <p class="mb-2"><strong>Description:</strong> {{ $product->description }}</p>
        <p class="mb-1"><strong>User:</strong> {{ $product->user?->name }} ({{ $product->user?->email }})</p>
        <p class="mb-1"><strong>Brand:</strong> {{ $product->brand ?? '-' }}</p>
        <p class="mb-1"><strong>SKU:</strong> {{ $product->sku ?? '-' }}</p>
        <p class="mb-1"><strong>Price:</strong> {{ $product->price ?? '-' }}</p>
        <p class="mb-1"><strong>Stock:</strong> {{ $product->stock ?? '-' }}</p>
        <p class="mb-1"><strong>Status:</strong> {{ $product->status }}</p>
        <p class="mb-1"><strong>Predicted:</strong> {{ $product->predictedCategory?->name ?? '-' }}</p>
        <p class="mb-1"><strong>Final:</strong> {{ $product->finalCategory?->name ?? '-' }}</p>
        <p class="mb-1"><strong>Confidence:</strong> {{ $product->ai_confidence ? number_format($product->ai_confidence, 2) : '-' }}</p>
        <p class="mb-0"><strong>Reviewed:</strong> {{ $product->admin_reviewed ? 'Yes' : 'No' }}</p>
    </div>
</div>
@endsection
