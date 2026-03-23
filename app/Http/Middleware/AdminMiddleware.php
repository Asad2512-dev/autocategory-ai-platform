<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class AdminMiddleware
{
    /**
     * Handle an incoming request.
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    public function handle(Request $request, Closure $next): Response
    {
        $user = $request->user();

        $wantsJson = $request->expectsJson() || $request->is('api/*');

        if (! $user) {
            if ($wantsJson) {
                return response()->json([
                    'success' => false,
                    'message' => 'Unauthenticated.',
                    'errors' => null,
                ], 401);
            }

            return redirect()->guest(route('admin.login'));
        }

        if (! $user->isAdmin() || $user->status !== 'active') {
            if ($wantsJson) {
                return response()->json([
                    'success' => false,
                    'message' => 'Forbidden: admin access required.',
                    'errors' => null,
                ], 403);
            }

            abort(403, 'Forbidden: admin access required.');
        }

        return $next($request);
    }
}
