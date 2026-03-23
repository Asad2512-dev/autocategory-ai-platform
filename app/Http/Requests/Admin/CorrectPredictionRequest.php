<?php

namespace App\Http\Requests\Admin;

use App\Http\Requests\ApiFormRequest;

class CorrectPredictionRequest extends ApiFormRequest
{
    /**
     * Get the validation rules that apply to the request.
     *
     * @return array<string, \Illuminate\Contracts\Validation\ValidationRule|array<mixed>|string>
     */
    public function rules(): array
    {
        return [
            'final_category_id' => ['required', 'integer', 'exists:categories,id'],
        ];
    }
}
