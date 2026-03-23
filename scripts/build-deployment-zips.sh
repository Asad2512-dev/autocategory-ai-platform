#!/usr/bin/env bash
# Build autocategory-laravel.zip and autocategory-fastapi.zip from this monorepo.
# Run from repository root: bash scripts/build-deployment-zips.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/dist}"
mkdir -p "$OUT"

LZIP="$OUT/autocategory-laravel.zip"
FZIP="$OUT/autocategory-fastapi.zip"

rm -f "$LZIP" "$FZIP"

(
  cd "$ROOT"
  zip -r "$LZIP" . \
    -x ".git/*" \
    -x ".git/**/*" \
    -x "vendor/*" \
    -x "vendor/**/*" \
    -x "node_modules/*" \
    -x "node_modules/**/*" \
    -x ".venv/*" \
    -x ".venv/**/*" \
    -x "tests/*" \
    -x "tests/**/*" \
    -x "phpunit.xml" \
    -x ".phpunit.result.cache" \
    -x "database/*.sqlite" \
    -x "database/**/*.sqlite" \
    -x ".DS_Store" \
    -x "bootstrap/cache/*.php" \
    -x "storage/logs/*" \
    -x "storage/logs/**/*" \
    -x ".env" \
    -x ".env.backup" \
    -x ".env.production" \
    -x "ml-service/*" \
    -x "ml-service/**/*" \
    -x "dist/*" \
    -x "dist/**/*" \
    -x "*.zip"
)

(
  cd "$ROOT/ml-service"
  zip -r "$FZIP" . \
    -x ".git/*" \
    -x ".git/**/*" \
    -x ".venv/*" \
    -x ".venv/**/*" \
    -x "__pycache__/*" \
    -x "**/__pycache__/*" \
    -x ".env" \
    -x ".env.backup" \
    -x ".pytest_cache/*" \
    -x ".pytest_cache/**/*" \
    -x "tests/*" \
    -x "tests/**/*" \
    -x "data/training_dataset.csv" \
    -x "data/training_dataset.cleaned.csv" \
    -x "data/training_dataset2.csv" \
    -x "data/training_dataset2.cleaned.csv" \
    -x "data/training_dataset3.csv" \
    -x "data/final_merged_cleaned_dataset.csv" \
    -x "train_model.py" \
    -x "scripts/clean_dataset.py" \
    -x "*.pyc" \
    -x ".mypy_cache/*" \
    -x ".ruff_cache/*"
)

echo "Wrote:"
echo "  $LZIP"
echo "  $FZIP"
