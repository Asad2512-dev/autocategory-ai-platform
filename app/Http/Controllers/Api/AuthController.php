<?php

namespace App\Http\Controllers\Api;

use App\Http\Requests\Auth\LoginRequest;
use App\Http\Requests\Auth\RegisterRequest;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Hash;

class AuthController extends ApiController
{
    public function register(RegisterRequest $request): JsonResponse
    {
        $user = User::query()->create([
            'name' => $request->name,
            'email' => $request->email,
            'password' => $request->password,
            'role' => 'user',
            'status' => 'active',
        ]);

        $token = $user->createToken('mobile-token')->plainTextToken;

        return $this->successResponse('Registration successful.', [
            'token' => $token,
            'user' => $user,
        ], 201);
    }

    public function login(LoginRequest $request): JsonResponse
    {
        $user = User::query()->where('email', $request->email)->first();

        if (! $user || ! Hash::check($request->password, $user->password)) {
            return $this->errorResponse('Invalid credentials.', null, 422);
        }

        $token = $user->createToken('mobile-token')->plainTextToken;

        return $this->successResponse('Login successful.', [
            'token' => $token,
            'user' => $user,
        ]);
    }

    public function logout(): JsonResponse
    {
        request()->user()?->currentAccessToken()?->delete();

        return $this->successResponse('Logout successful.');
    }

    public function profile(): JsonResponse
    {
        return $this->successResponse('Profile fetched successfully.', request()->user());
    }
}
