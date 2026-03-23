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
            if (! Schema::hasColumn('prediction_logs', 'feedback_exported')) {
                $table->boolean('feedback_exported')->default(false)->after('corrected_by_admin');
            }

            if (! Schema::hasColumn('prediction_logs', 'feedback_export_failed')) {
                $table->boolean('feedback_export_failed')->default(false)->after('feedback_exported');
            }

            if (! Schema::hasColumn('prediction_logs', 'feedback_exported_at')) {
                $table->timestamp('feedback_exported_at')->nullable()->after('feedback_export_failed');
            }

            if (! Schema::hasColumn('prediction_logs', 'feedback_export_error')) {
                $table->text('feedback_export_error')->nullable()->after('feedback_exported_at');
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
                'feedback_export_error',
                'feedback_exported_at',
                'feedback_export_failed',
                'feedback_exported',
            ];

            foreach ($columns as $column) {
                if (Schema::hasColumn('prediction_logs', $column)) {
                    $table->dropColumn($column);
                }
            }
        });
    }
};
