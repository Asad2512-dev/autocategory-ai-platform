# Architecture

## What this is

AutoCategory AI Platform. Laravel backend + FastAPI ML microservice for product categorization.

## Layout

- `app/` — `Http`, `Jobs`, `Models`, `Providers`, `Services`
- `bootstrap/`
- `config/`
- `database/`
- `deploy/`
- `deploy_bundle/`
- `ml-service/` — `.env.example`, `.gitignore`, `app`, `autocategory-fastapi-deploy.zip`, `data`, `deploy_bundle`, `LIVE_DEPLOY_CHECKLIST.md`, `main.py` (+10 more)
- `postman/`
- `public/`
- `resources/`
- `routes/` — `api.php`, `console.php`, `web.php`
- `scripts/`
- `storage/`
- `tests/`
- Tooling: `.editorconfig`, `.env.example`, `.env.production.example`, `.gitattributes`, `.gitignore`
- Root files: `artisan`, `composer.json`, `composer.lock`, `package-lock.json`, `package.json`, `phpunit.xml`, `postcss.config.js`, `README.md`, `tailwind.config.js`, `vite.config.js`

## How the pieces fit

Laravel application: `artisan` and `composer.json` are at the root, and PHP code is under `app/` (Http, Jobs, Models, Providers, Services). Route files: `routes/api.php`, `routes/console.php`, `routes/web.php`. Views and frontend source are under `resources/`. Migrations and seeders are under `database/`. Composer requires Laravel Sanctum. The root `package.json` builds frontend assets with Vite. `ml-service/` is a Python project (`ml-service/requirements.txt`; FastAPI).

## How to run

Commands written in the README:

```
composer install
cp .env.example .env
php artisan key:generate
php artisan migrate
```

```
npm install
npm run dev
```

Scripts in the root `package.json`:

- `build` — `vite build`
- `dev` — `vite`

Composer scripts: `dev`.

## External services named in the repo

- Redis — `REDIS_CLIENT` in `.env.example`
- AWS — `AWS_ACCESS_KEY_ID` in `.env.example`
