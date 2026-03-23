# AutoCategory AI Platform

Laravel backend + FastAPI ML microservice for product categorization.

## Project Structure

- `app/`, `routes/`, `config/`, `database/`: Laravel API/application code
- `ml-service/`: FastAPI service for category prediction
- `ml-service/app/`: FastAPI app modules
- `ml-service/model/`: trained model artifacts used by FastAPI
- `public/`, `resources/`: Laravel web assets

## Tech Stack

- **Backend API:** Laravel 11 (PHP 8.2+)
- **ML Service:** FastAPI + scikit-learn (Python 3.11+ recommended)
- **Frontend tooling:** Vite + Tailwind
- **Database:** MySQL (default in examples)

## Local Development Setup

### 1) Laravel dependencies

```bash
composer install
cp .env.example .env
php artisan key:generate
php artisan migrate
```

### 2) Frontend dependencies (optional, for assets)

```bash
npm install
npm run dev
```

### 3) FastAPI dependencies

```bash
cd ml-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Services

### Laravel API

```bash
php artisan serve
```

### FastAPI ML service

```bash
cd ml-service
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

## Environment Variables

- Laravel examples:
  - `.env.example` (local)
  - `.env.production.example` (production template)
- FastAPI example:
  - `ml-service/.env.example`

Never commit `.env` files or secrets. Fill local values manually after copying example files.

## Git Hygiene

This repository is configured to keep generated/local files out of git, including:

- `.env` and secret variants
- `vendor/`
- `.venv/` and `ml-service/.venv/`
- `node_modules/`
- build output (`dist/`, `build/`)
- logs and `*.zip` archives

## Deployment Notes

Deployment-oriented docs for the ML service are in `ml-service/TRAINING_AND_DEPLOYMENT.md` and `ml-service/LIVE_DEPLOY_CHECKLIST.md`.
