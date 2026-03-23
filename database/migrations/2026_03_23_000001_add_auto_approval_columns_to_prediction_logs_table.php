<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('prediction_logs', function (Blueprint $table) {
            if (! Schema::hasColumn('prediction_logs', 'suggested_new_category')) {
                $table->text('suggested_new_category')->nullable()->after('top_candidates');
            }
            if (! Schema::hasColumn('prediction_logs', 'auto_approved')) {
                $table->boolean('auto_approved')->default(false)->after('corrected_by_admin');
            }
        });
    }

    public function down(): void
    {
        Schema::table('prediction_logs', function (Blueprint $table) {
            if (Schema::hasColumn('prediction_logs', 'auto_approved')) {
                $table->dropColumn('auto_approved');
            }
            if (Schema::hasColumn('prediction_logs', 'suggested_new_category')) {
                $table->dropColumn('suggested_new_category');
            }
        });
    }
};
