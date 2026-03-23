<?php

namespace Database\Seeders;

use App\Models\Category;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

class CategorySeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        $categories = [
            'Electronics',
            'Fashion',
            'Books',
            'Home',
            'Home & Kitchen',
            'Beauty',
            'Sports',
            'Toys',
        ];

        foreach ($categories as $name) {
            Category::query()->updateOrCreate(
                ['name' => $name],
                [
                    'slug' => Str::slug($name),
                    'description' => $name.' category',
                    'status' => 'active',
                ]
            );
        }
    }
}
