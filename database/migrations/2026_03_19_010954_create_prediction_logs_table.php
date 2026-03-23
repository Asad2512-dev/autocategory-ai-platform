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
        if (Schema::hasTable('prediction_logs')) {
            return;
        }

        Schema::create('prediction_logs', function (Blueprint $table) {
            $table->id();
            $table->foreignId('product_id')->constrained()->cascadeOnDelete();
            $table->string('input_title');
            $table->text('input_description');
            $table->string('predicted_category_name');
            $table->decimal('confidence', 5, 4);
            $table->boolean('low_confidence')->default(false);
            $table->boolean('review_needed')->default(false);
            $table->boolean('flagged_for_retraining')->default(false);
            $table->string('prediction_source')->nullable();
            $table->text('message')->nullable();
            $table->json('top_candidates')->nullable();
            $table->string('final_category_name')->nullable();
            $table->boolean('corrected_by_admin')->default(false);
            $table->boolean('feedback_exported')->default(false);
            $table->boolean('feedback_export_failed')->default(false);
            $table->timestamp('feedback_exported_at')->nullable();
            $table->text('feedback_export_error')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        if (! Schema::hasTable('prediction_logs')) {
            return;
        }

        Schema::dropIfExists('prediction_logs');
    }
};
