<?php

namespace App\Http\Requests\Product;

use App\Http\Requests\ApiFormRequest;

class StoreProductRequest extends ApiFormRequest
{
    /**
     * Get the validation rules that apply to the request.
     *
     * @return array<string, \Illuminate\Contracts\Validation\ValidationRule|array<mixed>|string>
     */
    public function rules(): array
    {
        return [
            'title' => ['required', 'string', 'max:255'],
            'description' => ['required', 'string'],
            'brand' => ['nullable', 'string', 'max:100'],
            'sku' => ['nullable', 'string', 'max:100', 'unique:products,sku'],
            'price' => ['nullable', 'numeric', 'min:0'],
            'stock' => ['nullable', 'integer', 'min:0'],
            'image' => ['nullable', 'url', 'max:255'],
            'status' => ['nullable', 'in:active,inactive'],
            'trigger_prediction' => ['nullable', 'boolean'],
            'prediction_mode' => ['nullable', 'in:sync,async'],
        ];
    }
}
