# Deployment zip contents — AutoCategory AI

Monorepo on disk: **`product-categorization-backend/`** (Laravel root) with **`ml-service/`** nested inside it. Two separate zips are built so CloudPanel gets only PHP and `/opt` gets only Python.

## Build

From the Laravel root:

```bash
bash scripts/build-deployment-zips.sh
```

Default output:

- `dist/autocategory-laravel.zip`
- `dist/autocategory-fastapi.zip`

---

## `autocategory-laravel.zip`

**Source directory:** Laravel root  
`/Applications/MAMP/htdocs/product-categorization-backend` (your path may differ).

**Purpose:** Laravel 11 (API, Sanctum, Blade admin). Run `composer install` on the server.

**Included (typical):** `app/`, `bootstrap/`, `config/`, `database/` (migrations, seeders, factories), `public/`, `resources/`, `routes/`, `storage/` tree, `artisan`, `composer.json`, `composer.lock`, `deploy/`, `scripts/`, root `.env.example`, `.env.production.example`, `DEPLOYMENT.md`, `API_DOCUMENTATION.md`, etc.

**Excluded by `scripts/build-deployment-zips.sh`:**

| Pattern | Reason |
|--------|--------|
| `vendor/`, `node_modules/` | Install on VPS |
| `.venv/` at **Laravel root** | Stray Python venv (~hundreds of MB); not part of Laravel |
| `ml-service/` | Entire FastAPI tree — separate zip |
| `tests/`, `phpunit.xml`, `.phpunit.result.cache` | Dev-only |
| `database/*.sqlite` | Local SQLite; production uses MySQL |
| `storage/logs/*` | Runtime logs |
| `.env`, `.env.backup`, `.env.production` | Secrets |
| `bootstrap/cache/*.php` | Regenerate with `php artisan config:cache` |
| `dist/*`, `*.zip` | Build artifacts |
| `.git/`, `.DS_Store` | VCS / junk |

**On the server:** `composer install --no-dev --optimize-autoloader`, then copy `deploy/laravel.env.example` → `.env` and edit.

---

## `autocategory-fastapi.zip`

**Source directory:**  
`/Applications/MAMP/htdocs/product-categorization-backend/ml-service`

**Purpose:** FastAPI app (`app.main:app`), `requirements.txt`, feedback CSV, model artifacts.

**Included:** `app/`, `requirements.txt`, `main.py`, `README.md`, `.env.example`, `data/feedback_corrections.csv`, `model/` (including **`model.pkl`**, **`vectorizer.pkl`**, **`label_encoder.pkl`** when present in your workspace — the script does **not** strip `.pkl` files).

**Excluded:**

| Pattern | Reason |
|--------|--------|
| `.venv/`, `__pycache__/`, `*.pyc` | Recreate / runtime |
| `.env`, `.env.backup` | Secrets |
| `tests/` | Dev-only |
| `data/training_dataset*.csv`, `data/final_merged_cleaned_dataset.csv` | Large training data; not needed to serve predictions |
| `train_model.py`, `scripts/clean_dataset.py` | Training-only |

**On the server:** extract to `/opt/autocategory-fastapi`, create `.venv`, `pip install -r requirements.txt`, then create `.env`:

- Prefer copying **`deploy/fastapi.env.example`** from the **Laravel** deployment (same repo; that file is not inside the FastAPI zip), **or**
- Start from `ml-service/.env.example` in the FastAPI zip and set `MODEL_DIR` / `FEEDBACK_DATASET_PATH` to `/opt/autocategory-fastapi/...`.

If your zip was built **without** pickles (custom zip), copy `*.pkl` into `MODEL_DIR` manually.

---

## Path cheat sheet

| Environment | Laravel root | FastAPI root |
|-------------|--------------|---------------|
| Local (this repo) | `.../product-categorization-backend` | `.../product-categorization-backend/ml-service` |
| VPS (example) | CloudPanel site root (contains `artisan`) | `/opt/autocategory-fastapi` |

Laravel calls FastAPI at **`http://127.0.0.1:8001`** via `ML_SERVICE_BASE_URL` / `AI_SERVICE_URL`.
