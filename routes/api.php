<?php

use App\Http\Controllers\Api\CategoryController;
use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\Admin\PredictionReviewController;
use App\Http\Controllers\Api\ProductController;
use Illuminate\Support\Facades\Route;

Route::post('/register', [AuthController::class, 'register']);
Route::post('/login', [AuthController::class, 'login']);

Route::middleware('auth:sanctum')->group(function () {
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/profile', [AuthController::class, 'profile']);

    Route::get('/categories', [CategoryController::class, 'index']);

    Route::get('/products', [ProductController::class, 'index']);
    Route::post('/products', [ProductController::class, 'store']);
    Route::get('/products/{product}', [ProductController::class, 'show']);
    Route::put('/products/{product}', [ProductController::class, 'update']);
    Route::delete('/products/{product}', [ProductController::class, 'destroy']);
    Route::post('/products/{product}/predict', [ProductController::class, 'predict']);

    Route::prefix('admin')->middleware('admin')->group(function () {
        Route::get('/predictions', [PredictionReviewController::class, 'index']);
        Route::post('/predictions/{product}/approve', [PredictionReviewController::class, 'approve']);
        Route::post('/predictions/{product}/correct', [PredictionReviewController::class, 'correct']);
        Route::post('/predictions/{predictionLog}/retry-feedback-export', [PredictionReviewController::class, 'retryFeedbackExport']);
        Route::post('/predictions/retry-failed-feedback-exports', [PredictionReviewController::class, 'retryFailedFeedbackExports']);
    });
});
