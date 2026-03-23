@extends('admin.layouts.app')

@section('content')
<h3 class="mb-3">Predictions <span class="text-muted small fw-normal">(read-only)</span></h3>

<div class="card shadow-sm">
    <div class="table-responsive">
        <table class="table table-striped mb-0">
            <thead>
            <tr>
                <th>ID</th>
                <th>Product</th>
                <th>Predicted</th>
                <th>Confidence</th>
                <th>Reviewed</th>
                <th>Final</th>
                <th>Feedback Export</th>
            </tr>
            </thead>
            <tbody>
            @forelse($products as $product)
                @php
                    $latestLog = $product->latestPredictionLog;
                @endphp
                <tr>
                    <td>{{ $product->id }}</td>
                    <td>{{ $product->title }}</td>
                    <td>{{ $product->predictedCategory?->name ?? 'Unknown' }}</td>
                    <td>{{ $product->ai_confidence ? number_format($product->ai_confidence, 2) : '-' }}</td>
                    <td>
                        @if($product->admin_reviewed)
                            <span class="badge bg-success">Yes</span>
                        @else
                            <span class="badge bg-warning text-dark">No</span>
                        @endif
                    </td>
                    <td>{{ $product->finalCategory?->name ?? '-' }}</td>
                    <td>
                        @if(! $latestLog)
                            <span class="badge bg-secondary">No Log</span>
                        @elseif(! $latestLog->corrected_by_admin)
                            <span class="badge bg-secondary">N/A</span>
                        @elseif($latestLog->feedback_exported)
                            <span class="badge bg-success">Exported</span>
                        @elseif($latestLog->feedback_export_failed)
                            <span class="badge bg-danger">Failed</span>
                            @if($latestLog->feedback_export_error)
                                <div class="small text-danger mt-1">{{ $latestLog->feedback_export_error }}</div>
                            @endif
                        @else
                            <span class="badge bg-warning text-dark">Pending</span>
                        @endif
                    </td>
                </tr>
            @empty
                <tr><td colspan="7" class="text-center py-4">No predictions available.</td></tr>
            @endforelse
            </tbody>
        </table>
    </div>
</div>

<div class="mt-3">{{ $products->links() }}</div>
@endsection
