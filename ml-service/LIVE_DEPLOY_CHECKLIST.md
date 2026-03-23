# Live server deployment checklist (AutoCategory AI)

Use this when promoting new ML artifacts or a new FastAPI build to production. Paths match your current layout.

## Reference paths

| Component | Path |
|-----------|------|
| Laravel (web root) | `/home/deploy/htdocs/autocategoryai.online` |
| FastAPI app root | `/opt/autocategory-fastapi` |
| FastAPI model dir (default) | `/opt/autocategory-fastapi/model` |
| Laravel → ML internal URL | `http://127.0.0.1:8001` (from `.env`: `ML_SERVICE_BASE_URL` / `AI_SERVICE_URL`) |
| systemd unit | `/etc/systemd/system/autocategory-fastapi.service` |
| Queue worker | `/etc/supervisor/conf.d/autocategory-queue.conf` |

---

## Pre-deploy

- [ ] Trained locally or on a build host with **same** Python + `scikit-learn` major version as production (avoid pickle incompatibility).
- [ ] Artifacts present: `model.pkl`, `vectorizer.pkl`, `label_encoder.pkl`.
- [ ] Optional but recommended: `model_info.json`, `class_labels.json` (for `GET /model-info` and ops visibility).
- [ ] Report files (`model_comparison.csv`, `metrics.json`) are **not** required for runtime; keep them for your report/backup only.

## Backup (on server)

```bash
sudo cp -a /opt/autocategory-fastapi/model /opt/autocategory-fastapi/model.bak.$(date +%Y%m%d%H%M)
```

## Deploy artifacts

From the directory containing the new files:

```bash
sudo install -m 644 model.pkl vectorizer.pkl label_encoder.pkl /opt/autocategory-fastapi/model/
sudo install -m 644 model_info.json class_labels.json /opt/autocategory-fastapi/model/ 2>/dev/null || true
```

## Restart FastAPI

```bash
sudo systemctl restart autocategory-fastapi
sudo systemctl status autocategory-fastapi --no-pager
```

## Smoke tests (from server)

```bash
curl -sS http://127.0.0.1:8001/health
curl -sS http://127.0.0.1:8001/model-info
curl -sS -X POST http://127.0.0.1:8001/predict \
  -H "Content-Type: application/json" \
  -d '{"title":"Test earbuds","description":"Wireless bluetooth headphones"}'
```

Expect `/health` → `"status":"ok"` when artifacts load; `/predict` → JSON with `predicted_category`, `confidence`, `top_candidates`, `prediction_source`, `message`, booleans as before.

## Laravel / app

- [ ] `.env` on Laravel host still has `ML_SERVICE_BASE_URL=http://127.0.0.1:8001` (or your correct internal URL).
- [ ] No Laravel deploy required **only** for pickle/metadata updates if API contract unchanged.
- [ ] After FastAPI restart, create or update one product through the app and confirm prediction + logs (queue workers do not need restart **unless** you changed Laravel code).

## Supervisor (only if needed)

- [ ] Restart queue workers **only** if you deployed Laravel changes that affect jobs:  
  `sudo supervisorctl reread && sudo supervisorctl update && sudo supervisorctl restart autocategory-queue:*`  
  (exact program names as in `autocategory-queue.conf`.)

## Rollback

```bash
sudo rm -rf /opt/autocategory-fastapi/model
sudo mv /opt/autocategory-fastapi/model.bak.YYYYMMDDHHMM /opt/autocategory-fastapi/model
sudo systemctl restart autocategory-fastapi
curl -sS http://127.0.0.1:8001/health
```

## If `MODEL_DIR` is set

If `autocategory-fastapi.service` sets `Environment=MODEL_DIR=...`, deploy files to **that** directory instead of `/opt/autocategory-fastapi/model`.
