import logging
from typing import Any

from fastapi import FastAPI, HTTPException

from app.core.config import settings
from app.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    GeminiFallbackCheckRequest,
    GeminiFallbackCheckResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
)
from app.services.gemini_fallback import GeminiFallbackService
from app.services.predictor import PredictorService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Product Categorization ML Service",
    version="1.0.0",
    description="FastAPI microservice for e-commerce product category prediction.",
)

predictor = PredictorService(
    model_dir=settings.model_dir,
    known_categories=settings.known_categories,
    model_confidence_threshold=settings.model_confidence_threshold,
    very_low_confidence_threshold=settings.very_low_confidence_threshold,
    feedback_dataset_path=settings.feedback_dataset_path,
    gemini_force_verify=settings.gemini_force_verify,
    gemini_service=GeminiFallbackService(
        enabled=settings.gemini_enabled,
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.gemini_timeout_seconds,
        allowed_categories=settings.known_categories,
    ),
)


@app.on_event("startup")
def startup_event() -> None:
    logger.info(
        "Starting ML service. model_dir=%s model_threshold=%s very_low_threshold=%s gemini_enabled=%s gemini_force_verify=%s",
        settings.model_dir,
        settings.model_confidence_threshold,
        settings.very_low_confidence_threshold,
        settings.gemini_enabled,
        settings.gemini_force_verify,
    )
    predictor.load_artifacts()


@app.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    return ModelInfoResponse(**predictor.get_model_info_public())


@app.get("/health")
def health_check() -> dict[str, Any]:
    artifact_status = {
        "model": predictor.model_path.exists(),
        "vectorizer": predictor.vectorizer_path.exists(),
        "label_encoder": predictor.label_encoder_path.exists(),
    }

    if predictor.ready:
        return {
            "status": "ok",
            "reason": None,
            "model_dir": str(settings.model_dir),
            "model_confidence_threshold": settings.model_confidence_threshold,
            "very_low_confidence_threshold": settings.very_low_confidence_threshold,
            "gemini_enabled": settings.gemini_enabled,
            "gemini_force_verify": settings.gemini_force_verify,
            "artifact_status": artifact_status,
        }

    return {
        "status": "error",
        "reason": predictor.error_message or "Model artifacts are not loaded",
        "model_dir": str(settings.model_dir),
        "model_confidence_threshold": settings.model_confidence_threshold,
        "very_low_confidence_threshold": settings.very_low_confidence_threshold,
        "gemini_enabled": settings.gemini_enabled,
        "gemini_force_verify": settings.gemini_force_verify,
        "artifact_status": artifact_status,
    }


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest) -> PredictResponse:
    if not predictor.ready:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Prediction service is not ready.",
                "reason": predictor.error_message or "Model artifacts are not loaded",
            },
        )

    try:
        result = predictor.predict(
            title=payload.title,
            description=payload.description,
            brand=payload.brand,
        )
        return PredictResponse(
            predicted_category=result.predicted_category,
            suggested_new_category=result.suggested_new_category,
            confidence=result.confidence,
            low_confidence=result.low_confidence,
            review_needed=result.review_needed,
            flagged_for_retraining=result.flagged_for_retraining,
            top_candidates=result.top_candidates,
            prediction_source=result.prediction_source,
            message=result.message,
        )
    except RuntimeError as exc:
        logger.error("Prediction attempted while service was not ready: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"message": "Prediction service is unavailable.", "reason": str(exc)},
        ) from exc
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(
            status_code=500,
            detail={"message": "Prediction failed.", "reason": str(exc)},
        ) from exc


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(payload: FeedbackRequest) -> FeedbackResponse:
    try:
        predictor.feedback_store.append_feedback_correction(payload.model_dump())
        return FeedbackResponse(saved=True, path=str(settings.feedback_dataset_path))
    except Exception as exc:
        logger.exception("Failed to persist feedback correction")
        raise HTTPException(
            status_code=500,
            detail={"message": "Feedback export failed.", "reason": str(exc)},
        ) from exc


@app.post("/debug/gemini-fallback-check", response_model=GeminiFallbackCheckResponse)
def debug_gemini_fallback_check(payload: GeminiFallbackCheckRequest) -> GeminiFallbackCheckResponse:
    logger.info(
        "Gemini debug endpoint called. title=%s brand=%s gemini_enabled=%s",
        payload.title,
        payload.brand,
        settings.gemini_enabled,
    )

    try:
        result = predictor.force_gemini_fallback_check(
            title=payload.title,
            description=payload.description,
            brand=payload.brand,
        )

        if result["success"]:
            logger.info("Gemini debug fallback check succeeded. category=%s", result["predicted_category"])
        else:
            logger.warning("Gemini debug fallback check failed. error=%s", result["error"])

        return GeminiFallbackCheckResponse(**result)
    except Exception as exc:
        logger.exception("Gemini debug fallback endpoint failed unexpectedly")
        return GeminiFallbackCheckResponse(
            success=False,
            gemini_enabled=settings.gemini_enabled,
            fallback_tested=False,
            prediction_source="gemini_fallback",
            predicted_category=None,
            suggested_new_category=None,
            confidence=None,
            review_needed=None,
            reason=None,
            raw_response_available=False,
            message="Gemini fallback check failed unexpectedly.",
            error=str(exc),
        )
