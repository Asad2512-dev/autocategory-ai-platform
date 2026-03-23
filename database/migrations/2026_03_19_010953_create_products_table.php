<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('products', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('title');
            $table->string('slug')->unique();
            $table->text('description');
            $table->string('brand')->nullable();
            $table->string('sku')->nullable()->unique();
            $table->decimal('price', 12, 2)->nullable();
            $table->unsignedInteger('stock')->nullable();
            $table->string('image')->nullable();
            $table->foreignId('predicted_category_id')->nullable()->constrained('categories')->nullOnDelete();
            $table->foreignId('final_category_id')->nullable()->constrained('categories')->nullOnDelete();
            $table->decimal('ai_confidence', 5, 4)->nullable();
            $table->boolean('is_ai_classified')->default(false);
            $table->boolean('admin_reviewed')->default(false);
            $table->string('status')->default('active');
            $table->timestamps();

            $table->index(['user_id', 'status']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('products');
    }
};
