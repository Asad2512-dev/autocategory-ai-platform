<?php

$providers = [
    App\Providers\AppServiceProvider::class,
];

if (class_exists(\Laravel\Pail\PailServiceProvider::class)) {
    $providers[] = \Laravel\Pail\PailServiceProvider::class;
}

return $providers;
