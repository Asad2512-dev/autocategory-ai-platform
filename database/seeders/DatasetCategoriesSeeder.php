<?php

namespace Database\Seeders;

use App\Models\Category;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

class DatasetCategoriesSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        $csvPath = base_path('ml-service/data/training_dataset2.cleaned.csv');

        if (! file_exists($csvPath)) {
            $this->command?->warn('Dataset file not found: '.$csvPath);

            return;
        }

        $handle = fopen($csvPath, 'r');

        if (! $handle) {
            $this->command?->warn('Unable to open dataset file.');

            return;
        }

        $header = fgetcsv($handle);

        if (! is_array($header)) {
            fclose($handle);
            $this->command?->warn('Dataset header row is missing.');

            return;
        }

        $categoryIndex = array_search('category', $header, true);

        if ($categoryIndex === false) {
            fclose($handle);
            $this->command?->warn('Dataset does not contain category column.');

            return;
        }

        $categories = [];

        while (($row = fgetcsv($handle)) !== false) {
            $raw = isset($row[$categoryIndex]) ? trim((string) $row[$categoryIndex]) : '';

            if ($raw !== '') {
                $categories[$raw] = true;
            }
        }

        fclose($handle);

        $names = array_keys($categories);
        sort($names);

        foreach ($names as $name) {
            Category::query()->updateOrCreate(
                ['name' => $name],
                [
                    'slug' => Str::slug($name),
                    'description' => $name.' category',
                    'status' => 'active',
                ]
            );
        }

        $this->command?->info('Imported '.count($names).' categories from dataset.');
    }
}
