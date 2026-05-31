import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.services.category_resolver import CategoryResolver
from app.services.feedback_store import FeedbackStore
from app.services.fallback_classifier import FallbackClassifier
from app.services.gemini_fallback import GeminiFallbackService, GeminiFallbackResult
from app.services.likely_wrong import is_likely_wrong_prediction

logger = logging.getLogger(__name__)


@dataclass
class PredictionPayload:
    predicted_category: str
    suggested_new_category: str | None
    confidence: float
    low_confidence: bool
    review_needed: bool
    flagged_for_retraining: bool
    top_candidates: list[dict[str, float | str]]
    prediction_source: str
    message: str


class PredictorService:
    def __init__(
        self,
        model_dir: Path,
        known_categories: tuple[str, ...],
        model_confidence_threshold: float,
        very_low_confidence_threshold: float,
        feedback_dataset_path: Path,
        gemini_service: GeminiFallbackService,
        gemini_force_verify: bool = False,
    ) -> None:
        self.model_dir = model_dir
        self.known_categories = known_categories
        self.model_confidence_threshold = model_confidence_threshold
        self.very_low_confidence_threshold = very_low_confidence_threshold
        self.gemini_force_verify = gemini_force_verify
        self.model: Any = None
        self.vectorizer: Any = None
        self.label_encoder: Any = None
        self.ready = False
        self.error_message: str | None = None
        self.category_resolver = CategoryResolver(known_categories=known_categories)
        self.fallback_classifier = FallbackClassifier(known_categories=known_categories)
        self.feedback_store = FeedbackStore(feedback_dataset_path=feedback_dataset_path)
        self.gemini_service = gemini_service
        self._model_info_blob: dict[str, Any] = {}

    @property
    def model_path(self) -> Path:
        return self.model_dir / "model.pkl"

    @property
    def vectorizer_path(self) -> Path:
        return self.model_dir / "vectorizer.pkl"

    @property
    def label_encoder_path(self) -> Path:
        return self.model_dir / "label_encoder.pkl"

    def load_artifacts(self) -> None:
        try:
            self._validate_paths()

            self.model = joblib.load(self.model_path)
            self.vectorizer = joblib.load(self.vectorizer_path)
            self.label_encoder = joblib.load(self.label_encoder_path)

            self._validate_artifacts()

            self._load_optional_model_info()

            self.ready = True
            self.error_message = None
            logger.info("Model artifacts loaded from %s", self.model_dir)
        except Exception as exc:
            self.ready = False
            self.error_message = str(exc)
            logger.exception("Failed to load model artifacts")

    def _validate_paths(self) -> None:
        if not self.model_dir.exists():
            raise FileNotFoundError(f"Model directory not found: {self.model_dir}")

        missing = [
            path.name
            for path in (self.model_path, self.vectorizer_path, self.label_encoder_path)
            if not path.exists()
        ]

        if missing:
            raise FileNotFoundError("Missing required model files: " + ", ".join(missing))

    def _validate_artifacts(self) -> None:
        if not hasattr(self.model, "predict"):
            raise TypeError("Invalid model artifact: missing 'predict' method")
        if not hasattr(self.vectorizer, "transform"):
            raise TypeError("Invalid vectorizer artifact: missing 'transform' method")
        if not hasattr(self.label_encoder, "inverse_transform"):
            raise TypeError("Invalid label_encoder artifact: missing 'inverse_transform' method")

    def _load_optional_model_info(self) -> None:
        info_path = self.model_dir / "model_info.json"
        if not info_path.exists():
            self._model_info_blob = {}
            return
        try:
            self._model_info_blob = json.loads(info_path.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("Could not parse model_info.json; continuing without metadata.")
            self._model_info_blob = {}

    @staticmethod
    def _softmax_from_logits(logits: np.ndarray) -> np.ndarray:
        arr = np.asarray(logits, dtype=float)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        shifted = arr - np.max(arr, axis=1, keepdims=True)
        exp = np.exp(shifted)
        return exp / np.sum(exp, axis=1, keepdims=True)

    def _predict_proba_matrix(self, features: Any) -> np.ndarray | None:
        """Return shape (n_samples, n_classes). None if unsupported or inconsistent with label_encoder."""
        classes = getattr(self.label_encoder, "classes_", None)
        n_classes = len(classes) if classes is not None else 0
        try:
            if hasattr(self.model, "predict_proba"):
                mat = np.asarray(self.model.predict_proba(features), dtype=float)
            elif hasattr(self.model, "decision_function"):
                scores = self.model.decision_function(features)
                mat = self._softmax_from_logits(np.asarray(scores, dtype=float))
            else:
                return None
        except Exception as exc:
            logger.warning("Model scoring failed (%s); continuing without probabilities.", exc)
            return None

        if mat.ndim != 2 or mat.shape[0] < 1:
            logger.warning("Unexpected score matrix shape %s; ignoring.", getattr(mat, "shape", None))
            return None
        row_sums = np.sum(mat, axis=1)
        if np.any(~np.isfinite(mat)) or np.any(row_sums <= 0):
            logger.warning("Non-finite or non-positive score rows; ignoring probability matrix.")
            return None
        if n_classes > 0 and mat.shape[1] != n_classes:
            logger.warning(
                "Score columns (%s) do not match label_encoder (%s classes); ignoring scores.",
                mat.shape[1],
                n_classes,
            )
            return None
        return mat

    def get_model_info_public(self) -> dict[str, Any]:
        """Serializable dict for GET /model-info (additive API surface)."""
        labels: list[str] = []
        if self.label_encoder is not None and hasattr(self.label_encoder, "classes_"):
            labels = [str(x) for x in self.label_encoder.classes_]

        blob = self._model_info_blob or {}
        name = str(blob.get("best_classifier", "") or "")
        if self.ready and self.model is not None and not name:
            name = self.model.__class__.__name__
        if not name:
            name = "unknown"

        return {
            "ready": self.ready,
            "model_name": name,
            "app_version": str(blob.get("fastapi_app_version", "1.0.0")),
            "num_labels": len(labels),
            "labels": labels,
            "model_dir": str(self.model_dir),
            "training_generated_at": blob.get("generated_at"),
            "error": None if self.ready else (self.error_message or "Model not loaded"),
        }

    @staticmethod
    def preprocess_text(title: str, description: str) -> str:
        text = f"{title} {description}".lower().strip()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def predict(self, title: str, description: str, brand: str | None = None) -> PredictionPayload:
        if not self.ready:
            reason = self.error_message or "Model artifacts are not loaded"
            raise RuntimeError(reason)

        processed_text = self.preprocess_text(title=title, description=description)
        features = self.vectorizer.transform([processed_text])

        encoded_prediction = self.model.predict(features)[0]
        raw_label = str(self.label_encoder.inverse_transform([encoded_prediction])[0])

        confidence = 0.0
        top_model_candidates: list[dict[str, float | str]] = []

        proba_matrix = self._predict_proba_matrix(features)
        if proba_matrix is not None and hasattr(self.label_encoder, "classes_"):
            row = proba_matrix[0]
            confidence = float(np.max(row))
            top_model_candidates = self._extract_top_candidates(row)
        else:
            logger.warning(
                "Model has no probability or decision scores; confidence and top candidates unavailable."
            )

        confidence = round(confidence, 4)
        very_low_confidence = self._is_very_low_confidence(confidence)

        predicted_label = self._normalize_category(raw_label)

        if not top_model_candidates:
            top_model_candidates = [{"category": predicted_label, "confidence": confidence}]

        likely_wrong = is_likely_wrong_prediction(
            processed_text,
            predicted_label,
            confidence,
            self.fallback_classifier,
        )

        if self.gemini_force_verify and self.gemini_service.is_available():
            forced = self._invoke_gemini(
                title=title,
                description=description,
                brand=brand,
                top_model_candidates=top_model_candidates,
                very_low_confidence=very_low_confidence,
                force_verify=True,
                ml_prediction=predicted_label,
                ml_confidence=confidence,
                likely_wrong=False,
            )
            if forced:
                return self._payload_from_gemini(
                    gem=forced,
                    top_model_candidates=top_model_candidates,
                    very_low_confidence=very_low_confidence,
                    model_label=predicted_label,
                    force_verify_mode=True,
                )

        trust_model = confidence >= self.model_confidence_threshold and not likely_wrong

        if trust_model:
            return PredictionPayload(
                predicted_category=predicted_label,
                suggested_new_category=None,
                confidence=confidence,
                low_confidence=False,
                review_needed=False,
                flagged_for_retraining=False,
                top_candidates=top_model_candidates[:3],
                prediction_source="model",
                message="Prediction generated from model.",
            )

        logger.info(
            "Escalation path: confidence=%s threshold=%s category=%s likely_wrong=%s",
            confidence,
            self.model_confidence_threshold,
            predicted_label,
            likely_wrong,
        )

        keyword_matches = self.fallback_classifier.classify(processed_text)
        keyword_choice = self._select_keyword_fallback(keyword_matches, processed_text)

        contradicts = (
            bool(keyword_choice)
            and bool(keyword_choice["is_strong"])
            and str(keyword_choice["category"]) != predicted_label
        )
        weak_keyword = not keyword_choice or not keyword_choice["is_strong"]
        keyword_reinforces = (
            bool(keyword_choice)
            and bool(keyword_choice["is_strong"])
            and str(keyword_choice["category"]) == predicted_label
        )

        try_gemini = likely_wrong or contradicts or very_low_confidence
        if not keyword_reinforces:
            try_gemini = try_gemini or weak_keyword

        if try_gemini and self.gemini_service.is_available():
            gem = self._invoke_gemini(
                title=title,
                description=description,
                brand=brand,
                top_model_candidates=top_model_candidates,
                very_low_confidence=very_low_confidence,
                force_verify=False,
                ml_prediction=predicted_label,
                ml_confidence=confidence,
                likely_wrong=likely_wrong or contradicts,
            )
            if gem:
                return self._payload_from_gemini(
                    gem=gem,
                    top_model_candidates=top_model_candidates,
                    very_low_confidence=very_low_confidence,
                    model_label=predicted_label,
                    force_verify_mode=False,
                )

        if keyword_choice and keyword_choice["is_strong"]:
            kw_cat = str(keyword_choice["category"])
            return PredictionPayload(
                predicted_category=kw_cat,
                suggested_new_category=None,
                confidence=round(float(keyword_choice["confidence"]), 4),
                low_confidence=True,
                review_needed=True,
                flagged_for_retraining=True,
                top_candidates=top_model_candidates[:3],
                prediction_source="keyword_fallback",
                message="Keyword fallback used (Gemini unavailable or failed).",
            )

        if keyword_choice and keyword_choice["category"]:
            kw_cat = str(keyword_choice["category"])
            return PredictionPayload(
                predicted_category=kw_cat,
                suggested_new_category=None,
                confidence=round(float(keyword_choice["confidence"]), 4),
                low_confidence=True,
                review_needed=True,
                flagged_for_retraining=True,
                top_candidates=top_model_candidates[:3],
                prediction_source="keyword_fallback",
                message="Weak keyword signal; Gemini unavailable or failed.",
            )

        return PredictionPayload(
            predicted_category=predicted_label,
            suggested_new_category=None,
            confidence=confidence,
            low_confidence=True,
            review_needed=True,
            flagged_for_retraining=True,
            top_candidates=top_model_candidates[:3],
            prediction_source="model",
            message="Low confidence; no strong keyword or Gemini fallback.",
        )

    def _invoke_gemini(
        self,
        title: str,
        description: str,
        brand: str | None,
        top_model_candidates: list[dict[str, float | str]],
        very_low_confidence: bool,
        *,
        force_verify: bool,
        ml_prediction: str,
        ml_confidence: float,
        likely_wrong: bool,
    ) -> GeminiFallbackResult | None:
        return self.gemini_service.classify(
            title=title,
            description=description,
            brand=brand,
            ml_top_candidates=top_model_candidates,
            very_low_confidence=very_low_confidence,
            force_verify=force_verify,
            ml_prediction=ml_prediction,
            ml_confidence=ml_confidence,
            likely_wrong=likely_wrong,
        )

    def _payload_from_gemini(
        self,
        gem: GeminiFallbackResult,
        top_model_candidates: list[dict[str, float | str]],
        very_low_confidence: bool,
        model_label: str,
        force_verify_mode: bool,
    ) -> PredictionPayload:
        suggested = gem.suggested_new_category if very_low_confidence else None
        disagrees = gem.final_category != model_label
        if force_verify_mode:
            msg = "Gemini verification override (GEMINI_FORCE_VERIFY=true)."
            low = disagrees or gem.review_needed or very_low_confidence
        else:
            msg = "Gemini fallback used (low confidence, keyword clash, or likely-wrong heuristic)."
            low = True

        return PredictionPayload(
            predicted_category=gem.final_category,
            suggested_new_category=suggested,
            confidence=round(float(gem.confidence), 4),
            low_confidence=low,
            review_needed=bool(gem.review_needed) or (not force_verify_mode),
            flagged_for_retraining=True,
            top_candidates=top_model_candidates[:3],
            prediction_source="gemini_fallback",
            message=msg,
        )

    def force_gemini_fallback_check(
        self,
        title: str,
        description: str,
        brand: str | None = None,
    ) -> dict[str, Any]:
        processed_text = self.preprocess_text(title=title, description=description)
        top_model_candidates: list[dict[str, float | str]] = []
        very_low_confidence = True

        if self.ready:
            try:
                features = self.vectorizer.transform([processed_text])
                proba_matrix = self._predict_proba_matrix(features)
                if proba_matrix is not None and hasattr(self.label_encoder, "classes_"):
                    model_confidence = float(np.max(proba_matrix[0]))
                    top_model_candidates = self._extract_top_candidates(proba_matrix[0])
                    very_low_confidence = self._is_very_low_confidence(model_confidence)
            except Exception:
                logger.exception("Failed to compute optional model candidates for Gemini debug check")

        debug_result = self.gemini_service.classify_with_debug(
            title=title,
            description=description,
            brand=brand,
            ml_top_candidates=top_model_candidates,
            very_low_confidence=very_low_confidence,
        )

        if not debug_result.success or not debug_result.result:
            return {
                "success": False,
                "gemini_enabled": self.gemini_service.enabled,
                "fallback_tested": False,
                "prediction_source": "gemini_fallback",
                "predicted_category": None,
                "suggested_new_category": None,
                "confidence": None,
                "review_needed": None,
                "reason": None,
                "raw_response_available": debug_result.raw_response_available,
                "message": debug_result.message,
                "error": debug_result.error,
            }

        return {
            "success": True,
            "gemini_enabled": self.gemini_service.enabled,
            "fallback_tested": True,
            "prediction_source": "gemini_fallback",
            "predicted_category": debug_result.result.final_category,
            "suggested_new_category": debug_result.result.suggested_new_category,
            "confidence": round(float(debug_result.result.confidence), 4),
            "review_needed": debug_result.result.review_needed,
            "reason": debug_result.result.reason,
            "raw_response_available": debug_result.raw_response_available,
            "message": debug_result.message,
            "error": None,
        }

    def _is_very_low_confidence(self, confidence: float) -> bool:
        return confidence < self.very_low_confidence_threshold

    def _select_keyword_fallback(
        self,
        fallback_matches: list[Any],
        processed_text: str,
    ) -> dict[str, str | float | bool] | None:
        if not fallback_matches:
            return None

        top = fallback_matches[0]
        second_score = float(fallback_matches[1].score) if len(fallback_matches) > 1 else 0.0
        margin = float(top.score) - second_score
        strong_indicator = self.fallback_classifier.detect_strong_indicator(processed_text)

        is_strong = bool(strong_indicator == top.category) or (float(top.score) >= 0.55 and margin >= 0.20)
        is_ambiguous = margin < 0.12

        return {
            "category": self._normalize_category(str(top.category)),
            "confidence": float(top.score),
            "is_strong": is_strong and not is_ambiguous,
            "is_ambiguous": is_ambiguous,
        }

    def _normalize_category(self, category_name: str) -> str:
        return self.category_resolver.normalize(category_name) or category_name

    def _extract_top_candidates(self, probabilities_1d: np.ndarray) -> list[dict[str, float | str]]:
        if not hasattr(self.label_encoder, "classes_"):
            return []

        probabilities = np.asarray(probabilities_1d, dtype=float).reshape(-1)
        classes = [str(item) for item in self.label_encoder.classes_]
        top_indexes = np.argsort(probabilities)[::-1][:3]

        candidates: list[dict[str, float | str]] = []
        for index in top_indexes:
            category_name = classes[int(index)]
            normalized = self._normalize_category(category_name)
            candidates.append(
                {
                    "category": normalized,
                    "confidence": round(float(probabilities[int(index)]), 4),
                }
            )

        return candidates

    def build_feedback_record(self, title: str, description: str, final_category: str) -> dict[str, str]:
        # Future retraining hook: Laravel can persist these records when admin corrects predictions.
        return self.feedback_store.build_feedback_record(
            title=title,
            description=description,
            final_category=final_category,
        )
