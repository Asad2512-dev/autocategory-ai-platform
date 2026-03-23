# FastAPI ML Service

## Folder Structure

ml-service/
- app/
   - main.py
   - schemas.py
   - core/
      - config.py
   - services/
      - category_resolver.py
      - fallback_classifier.py
      - gemini_fallback.py
      - predictor.py
- main.py
- requirements.txt
- .env.example
- model/
   - model.pkl
   - vectorizer.pkl
   - label_encoder.pkl

## Setup

1. Create and activate virtual environment:
   - python3 -m venv .venv
   - source .venv/bin/activate
2. Install dependencies:
   - pip install -r requirements.txt
3. Place trained model artifacts in model/:
   - model.pkl
   - vectorizer.pkl
   - label_encoder.pkl
4. Run server:
    - uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

Optional custom model path:
- MODEL_DIR=/absolute/path/to/model uvicorn app.main:app --host 0.0.0.0 --port 8001

Optional env config (see `.env.example`):
- MODEL_CONFIDENCE_THRESHOLD=0.75
- VERY_LOW_CONFIDENCE_THRESHOLD=0.45
- GEMINI_ENABLED=true
- GEMINI_API_KEY=your_key_here
- GEMINI_MODEL=gemini-1.5-flash
- GEMINI_TIMEOUT_SECONDS=8

## Decision Flow

The predictor uses this order:

1. Model prediction first.
2. If confidence >= `MODEL_CONFIDENCE_THRESHOLD`, return model result (`prediction_source=model`).
3. If confidence is lower, run keyword fallback.
4. If keyword fallback is strong, return keyword result (`prediction_source=keyword_fallback`).
5. If keyword fallback is weak/ambiguous/not found, call Gemini.
6. If Gemini succeeds, return Gemini result (`prediction_source=gemini_fallback`).
7. If Gemini fails, gracefully return best available non-Gemini result.

Very low confidence behavior:

- If confidence < `VERY_LOW_CONFIDENCE_THRESHOLD`, Gemini may also return `suggested_new_category`.
- `predicted_category` always remains one of the fixed 10 categories.

## Train The Model (Phase 9)

See **TRAINING_AND_DEPLOYMENT.md** for full commands, `models/artifacts/` layout, production copy steps, and rollback.

CSV assumptions:
- Dataset is a CSV file.
- Required columns: title, description, category.
- Each row is one product sample.

Run training:

python train_model.py --data /absolute/path/to/dataset.csv

Optional flags:
- --test-size 0.2
- --random-state 42
- --report-dir models/artifacts (writes `model_comparison.csv`, `metrics.json` there)
- --semi-supervised --pseudo-confidence 0.92 (pseudo-label benchmark JSON)

Training pipeline includes:
- title + description combination
- basic text preprocessing
- label encoding for category
- train/test split
- TF-IDF vectorization
- comparison + tuning for Logistic Regression, Multinomial NB, Linear SVM, Random Forest
- evaluation with accuracy, precision, recall, F1-score
- printed classification report

Saved artifacts for FastAPI:
- ml-service/model/model.pkl
- ml-service/model/vectorizer.pkl
- ml-service/model/label_encoder.pkl
- ml-service/model/model_info.json (metadata for optional GET /model-info)
- ml-service/model/class_labels.json

Semester notebook (optional): `pip install -r requirements-notebook.txt` then open `notebooks/semester_project.ipynb`.

## Endpoints

- GET /health
- GET /model-info (optional; additive)
- POST /predict

## Quick HTTP Tests

GET /health

curl -sS http://127.0.0.1:8001/health

POST /predict

curl -sS -X POST http://127.0.0.1:8001/predict \\
   -H "Content-Type: application/json" \\
   -d '{
      "title": "Apple AirPods Pro",
      "description": "Wireless noise cancelling earbuds"
   }'

## Predict Request

{
  "title": "Apple AirPods Pro",
   "description": "Wireless noise cancelling earbuds",
   "brand": "Apple"
}

## Predict Response

{
  "predicted_category": "Electronics",
   "suggested_new_category": "Mobile Accessories > Earbuds",
   "confidence": 0.94,
   "low_confidence": true,
   "review_needed": false,
   "flagged_for_retraining": true,
   "top_candidates": [
      {"category": "Electronics", "confidence": 0.39},
      {"category": "Fashion", "confidence": 0.22}
   ],
   "prediction_source": "gemini_fallback",
   "message": "Low confidence model prediction. Gemini fallback used."
}

## Expected Behavior

Before real artifacts are placed:
- /health returns status = "error" with reason describing missing or invalid files.
- /predict returns HTTP 503 with a clean message and reason.

After real artifacts are placed:
- /health returns status = "ok".
- /predict returns predicted_category, suggested_new_category, confidence, low_confidence, review_needed, flagged_for_retraining, top_candidates, prediction_source, message.
- If model supports predict_proba, confidence is the max probability.
- If model confidence is low, keyword fallback and then Gemini fallback can be used.
- If Gemini fails, service returns a safe fallback result and does not crash.

## Laravel Integration Note

FastAPI base URL (Laravel .env):
- ML_SERVICE_BASE_URL=http://127.0.0.1:8001

Request payload Laravel should send:

{
   "title": "Product title",
   "description": "Product description",
   "brand": "Optional brand"
}

Response payload Laravel should expect:

{
   "predicted_category": "Electronics",
   "suggested_new_category": null,
   "confidence": 0.62,
   "low_confidence": true,
   "review_needed": true,
   "flagged_for_retraining": true,
   "top_candidates": [
      {"category": "Electronics", "confidence": 0.62},
      {"category": "Fashion", "confidence": 0.21}
   ],
   "prediction_source": "keyword_fallback",
   "message": "Low confidence model prediction. Strong keyword fallback used."
}

Laravel suggestion:
- If low_confidence=true, keep prediction for review flow and allow admin correction.
- Store top_candidates and prediction_source for audit and retraining datasets later.
