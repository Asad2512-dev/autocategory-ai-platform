# Training pipeline, artifacts, and production deployment

This document covers **local training**, **export paths**, and **deploying artifacts** to the live FastAPI service without changing Laravel or mobile API contracts.

**Production checklist (your server paths):** see [LIVE_DEPLOY_CHECKLIST.md](./LIVE_DEPLOY_CHECKLIST.md).

## Layout

| Path | Purpose |
|------|---------|
| `model/` | Default production artifacts: `model.pkl`, `vectorizer.pkl`, `label_encoder.pkl`, `model_info.json`, `class_labels.json`, `training_summary.json` |
| `models/artifacts/` | Optional reports: `model_comparison.csv`, `metrics.json`, `semi_supervised_metrics.json` (when using `--report-dir`) |
| `train_model.py` | Reproducible CLI: multi-model comparison, best-model export, optional pseudo-labeling benchmark |
| `notebooks/semester_project.ipynb` | Runnable report notebook (install `requirements-notebook.txt`) |

## Local training

From `ml-service/` with venv activated and dependencies from `requirements.txt`:

```bash
cd /path/to/ml-service
source .venv/bin/activate
pip install -r requirements.txt
```

Train on your CSV (columns: title, description, category — aliases supported):

```bash
python train_model.py --data data/your_dataset.csv --model-dir model
```

Write comparison tables to `models/artifacts/` while keeping pickles in `model/`:

```bash
python train_model.py --data data/your_dataset.csv --model-dir model --report-dir models/artifacts
```

Include semi-supervised (pseudo-labeling) before/after metrics:

```bash
python train_model.py --data data/your_dataset.csv --model-dir model --report-dir models/artifacts --semi-supervised --pseudo-confidence 0.92
```

Flags: `--test-size`, `--random-state`, `--export-cleaned`, `--show-top-features` (see `python train_model.py --help`).

## Models compared (same train/test split)

- Logistic Regression  
- Multinomial Naive Bayes  
- Linear SVM (`LinearSVC`)  
- Random Forest  

Metrics written to `model_comparison.csv` and `metrics.json` (weighted precision/recall/F1 and accuracy on the **test** split). The **best** model by weighted F1 (with tie-breaks in the printed summary) is saved as `model.pkl` + `vectorizer.pkl` + `label_encoder.pkl`.

## Production deployment (Linux example)

Paths match your live layout: FastAPI root `/opt/autocategory-fastapi`, systemd `autocategory-fastapi.service`.

1. **Backup current artifacts**

```bash
sudo cp -a /opt/autocategory-fastapi/model /opt/autocategory-fastapi/model.bak.$(date +%Y%m%d)
```

2. **Copy new files** (from your build machine or CI artifact):

```bash
sudo install -m 644 model/model.pkl model/vectorizer.pkl model/label_encoder.pkl model/model_info.json \
  /opt/autocategory-fastapi/model/
# optional
sudo install -m 644 model/class_labels.json model/training_summary.json /opt/autocategory-fastapi/model/
```

3. **Restart the service**

```bash
sudo systemctl restart autocategory-fastapi
curl -sS http://127.0.0.1:8001/health
curl -sS http://127.0.0.1:8001/model-info
```

`MODEL_DIR` can override the model directory if your unit file sets it.

## API compatibility

- `POST /predict` request/response schema is **unchanged**.  
- `GET /health` is **unchanged** (still reports `artifact_status` and load errors).  
- `GET /model-info` is **new and optional**; existing clients can ignore it.  
- **LinearSVC** and any model without `predict_proba` still work: the service derives scores from `decision_function` via a stable softmax so confidence and `top_candidates` remain populated.

## Rollback

```bash
sudo rm -rf /opt/autocategory-fastapi/model
sudo mv /opt/autocategory-fastapi/model.bak.YYYYMMDD /opt/autocategory-fastapi/model
sudo systemctl restart autocategory-fastapi
```

## Environment variables (unchanged)

See `.env.example` / existing docs: `MODEL_DIR`, `MODEL_CONFIDENCE_THRESHOLD`, `VERY_LOW_CONFIDENCE_THRESHOLD`, Gemini keys, etc. No new required variables were added.
