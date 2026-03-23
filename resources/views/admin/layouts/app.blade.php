<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Product Categorization Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
    <div class="container-fluid">
        <a class="navbar-brand" href="{{ route('admin.dashboard') }}">AI Categorization</a>
        <div class="navbar-nav flex-row flex-wrap align-items-center gap-2 gap-lg-3">
            <a class="nav-link" href="{{ route('admin.dashboard') }}">Dashboard</a>
            <a class="nav-link" href="{{ route('admin.categories.index') }}">Categories</a>
            <a class="nav-link" href="{{ route('admin.products.index') }}">Products</a>
            <a class="nav-link" href="{{ route('admin.predictions.index') }}">Predictions</a>
            <span class="navbar-text text-white-50 small d-none d-md-inline">{{ auth()->user()?->email }}</span>
            <form method="POST" action="{{ route('admin.logout') }}" class="d-inline ms-md-2">
                @csrf
                <button type="submit" class="btn btn-outline-light btn-sm">Log out</button>
            </form>
        </div>
    </div>
</nav>

<div class="container pb-5">
    @if (session('success'))
        <div class="alert alert-success">{{ session('success') }}</div>
    @endif

    @if ($errors->any())
        <div class="alert alert-danger">
            <ul class="mb-0">
                @foreach ($errors->all() as $error)
                    <li>{{ $error }}</li>
                @endforeach
            </ul>
        </div>
    @endif

    @yield('content')
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
