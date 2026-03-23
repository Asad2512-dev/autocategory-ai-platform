# Release checklist — AutoCategory AI

Use this before demos or grading submissions.

## Laravel

- [ ] `.env` on server matches `deploy/laravel.env.example` / `.env.production.example` (no `APP_DEBUG=true`).
- [ ] `APP_KEY` is set and unique.
- [ ] Database credentials match CloudPanel MySQL user.
- [ ] `ML_SERVICE_BASE_URL` (or `AI_SERVICE_URL`) is `http://127.0.0.1:8001`.
- [ ] `php artisan migrate --force` run after deploy.
- [ ] `php artisan config:cache` and `php artisan route:cache` after env changes.
- [ ] `storage:link` exists; `storage` and `bootstrap/cache` writable by PHP user.
- [ ] SSL certificate active in CloudPanel.
- [ ] Queue worker (Supervisor) running if you use async predictions.

## FastAPI

- [ ] `model.pkl`, `vectorizer.pkl`, `label_encoder.pkl` in `/opt/autocategory-fastapi/model`.
- [ ] `.env` present; `GEMINI_API_KEY` set only if `GEMINI_ENABLED=true`.
- [ ] `systemctl status autocategory-fastapi` is active.
- [ ] `curl -sS http://127.0.0.1:8001/health` returns `"status":"ok"`.

## Smoke tests

- [ ] HTTPS homepage loads.
- [ ] API login returns token.
- [ ] Creating a product returns prediction fields populated.
- [ ] Admin can approve or correct a prediction.
