<!doctype html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="AutoCategory AI — intelligent product categorization with Laravel and machine learning.">
    <title>{{ config('app.name', 'AutoCategory AI') }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .hero-gradient {
            background: linear-gradient(135deg, #1a1d21 0%, #2c3e50 50%, #1a252f 100%);
        }
    </style>
</head>
<body class="d-flex flex-column min-vh-100 bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm">
        <div class="container">
            <span class="navbar-brand fw-semibold">{{ config('app.name', 'AutoCategory AI') }}</span>
            <div class="navbar-nav ms-auto flex-row align-items-center gap-2 gap-lg-3">
                <span class="nav-link text-white-50 py-0 small d-none d-md-inline">JSON API · <code class="text-white-50">/api</code></span>
                <a class="btn btn-outline-light btn-sm" href="{{ route('admin.login') }}">Admin login</a>
            </div>
        </div>
    </nav>

    <header class="hero-gradient text-white py-5 py-lg-6">
        <div class="container py-lg-4">
            <p class="text-white-50 text-uppercase small mb-2 letter-spacing">Semester project</p>
            <h1 class="display-5 fw-bold mb-3">Smarter product categories, powered by AI</h1>
            <p class="lead text-white-75 col-lg-8 mb-4">
                AutoCategory AI combines a Laravel API, an admin review workflow, and a FastAPI ML service
                to predict categories, capture confidence, and improve over time with admin feedback.
            </p>
            <div class="d-flex flex-wrap gap-3">
                <a class="btn btn-light btn-lg" href="{{ route('admin.login') }}">Open admin dashboard</a>
                <a class="btn btn-outline-light btn-lg" href="{{ url('/up') }}">Health check</a>
            </div>
        </div>
    </header>

    <main class="container flex-grow-1 py-5">
        <div class="row g-4">
            <div class="col-md-4">
                <div class="card border-0 shadow-sm h-100">
                    <div class="card-body">
                        <h2 class="h5 card-title">REST API</h2>
                        <p class="card-text text-secondary small mb-0">
                            Sanctum-authenticated JSON API for registration, products, and predictions.
                            Base path: <code class="user-select-all">/api</code>
                        </p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card border-0 shadow-sm h-100">
                    <div class="card-body">
                        <h2 class="h5 card-title">Admin review</h2>
                        <p class="card-text text-secondary small mb-0">
                            Approve or correct AI suggestions and export feedback for model improvement.
                        </p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card border-0 shadow-sm h-100">
                    <div class="card-body">
                        <h2 class="h5 card-title">ML service</h2>
                        <p class="card-text text-secondary small mb-0">
                            Predictions run server-side; the ML layer is not exposed publicly on this site.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer class="border-top bg-white py-4 mt-auto">
        <div class="container text-center text-secondary small">
            &copy; {{ date('Y') }} {{ config('app.name', 'AutoCategory AI') }}
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
