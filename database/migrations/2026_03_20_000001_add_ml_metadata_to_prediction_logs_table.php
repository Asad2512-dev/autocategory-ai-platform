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
        if (! Schema::hasTable('prediction_logs')) {
            return;
        }

        Schema::table('prediction_logs', function (Blueprint $table) {
            if (! Schema::hasColumn('prediction_logs', 'low_confidence')) {
                $table->boolean('low_confidence')->default(false)->after('confidence');
            }

            if (! Schema::hasColumn('prediction_logs', 'review_needed')) {
                $table->boolean('review_needed')->default(false)->after('low_confidence');
            }

            if (! Schema::hasColumn('prediction_logs', 'flagged_for_retraining')) {
                $table->boolean('flagged_for_retraining')->default(false)->after('review_needed');
            }

            if (! Schema::hasColumn('prediction_logs', 'prediction_source')) {
                $table->string('prediction_source')->nullable()->after('flagged_for_retraining');
            }

            if (! Schema::hasColumn('prediction_logs', 'message')) {
                $table->text('message')->nullable()->after('prediction_source');
            }

            if (! Schema::hasColumn('prediction_logs', 'top_candidates')) {
                $table->json('top_candidates')->nullable()->after('message');
            }
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

        Schema::table('prediction_logs', function (Blueprint $table) {
            $columns = [
                'top_candidates',
                'message',
                'prediction_source',
                'flagged_for_retraining',
                'review_needed',
                'low_confidence',
            ];

            foreach ($columns as $column) {
                if (Schema::hasColumn('prediction_logs', $column)) {
                    $table->dropColumn($column);
                }
            }
        });
    }
};
