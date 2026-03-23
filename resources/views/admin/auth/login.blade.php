<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Admin Login — AutoCategory AI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center min-vh-100">
<div class="container" style="max-width: 420px;">
    <div class="card shadow-sm">
        <div class="card-body p-4">
            <h1 class="h4 mb-3 text-center">Admin sign in</h1>
            <p class="text-secondary small text-center mb-4">Read-only dashboard. Use API for product operations.</p>

            @if ($errors->any())
                <div class="alert alert-danger small">
                    {{ $errors->first() }}
                </div>
            @endif

            <form method="POST" action="{{ route('admin.login.store') }}">
                @csrf
                <div class="mb-3">
                    <label for="email" class="form-label">Email</label>
                    <input type="email" name="email" id="email" value="{{ old('email') }}" class="form-control" required autofocus autocomplete="username">
                </div>
                <div class="mb-3">
                    <label for="password" class="form-label">Password</label>
                    <input type="password" name="password" id="password" class="form-control" required autocomplete="current-password">
                </div>
                <div class="mb-3 form-check">
                    <input type="checkbox" name="remember" id="remember" value="1" class="form-check-input" {{ old('remember') ? 'checked' : '' }}>
                    <label class="form-check-label" for="remember">Remember me</label>
                </div>
                <button type="submit" class="btn btn-dark w-100">Sign in</button>
            </form>

            <p class="text-center mt-3 mb-0">
                <a href="{{ route('home') }}" class="small text-muted">← Back to site</a>
            </p>
        </div>
    </div>
</div>
</body>
</html>
