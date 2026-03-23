import json
import logging
from dataclasses import dataclass
from typing import Any
from urllib import error, request

logger = logging.getLogger(__name__)


@dataclass
class GeminiFallbackResult:
    final_category: str
    suggested_new_category: str | None
    reason: str
    confidence: float
    review_needed: bool


@dataclass
class GeminiDebugCallResult:
    success: bool
    result: GeminiFallbackResult | None
    error: str | None
    message: str
    raw_response_available: bool


class GeminiFallbackService:
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(
        self,
        enabled: bool,
        api_key: str,
        model: str,
        timeout_seconds: float,
        allowed_categories: tuple[str, ...],
    ) -> None:
        self.enabled = enabled
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.allowed_categories = allowed_categories

    def is_available(self) -> bool:
        return self.enabled and bool(self.api_key)

    def classify(
        self,
        title: str,
        description: str,
        brand: str | None,
        ml_top_candidates: list[dict[str, float | str]],
        very_low_confidence: bool,
        *,
        force_verify: bool = False,
        ml_prediction: str | None = None,
        ml_confidence: float | None = None,
        likely_wrong: bool = False,
    ) -> GeminiFallbackResult | None:
        debug_result = self.classify_with_debug(
            title=title,
            description=description,
            brand=brand,
            ml_top_candidates=ml_top_candidates,
            very_low_confidence=very_low_confidence,
            force_verify=force_verify,
            ml_prediction=ml_prediction,
            ml_confidence=ml_confidence,
            likely_wrong=likely_wrong,
        )
        return debug_result.result if debug_result.success else None

    def classify_with_debug(
        self,
        title: str,
        description: str,
        brand: str | None,
        ml_top_candidates: list[dict[str, float | str]],
        very_low_confidence: bool,
        *,
        force_verify: bool = False,
        ml_prediction: str | None = None,
        ml_confidence: float | None = None,
        likely_wrong: bool = False,
    ) -> GeminiDebugCallResult:
        if not self.enabled:
            return GeminiDebugCallResult(
                success=False,
                result=None,
                error="GEMINI_ENABLED is false.",
                message="Gemini fallback is disabled.",
                raw_response_available=False,
            )

        if not self.api_key:
            return GeminiDebugCallResult(
                success=False,
                result=None,
                error="GEMINI_API_KEY is missing.",
                message="Gemini API key is not configured.",
                raw_response_available=False,
            )

        prompt = self._build_prompt(
            title=title,
            description=description,
            brand=brand,
            ml_top_candidates=ml_top_candidates,
            very_low_confidence=very_low_confidence,
            force_verify=force_verify,
            ml_prediction=ml_prediction,
            ml_confidence=ml_confidence,
            likely_wrong=likely_wrong,
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        }

        url = f"{self.BASE_URL.format(model=self.model)}?key={self.api_key}"

        try:
            req = request.Request(
                url=url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")

            parsed = json.loads(body)
            text = self._extract_text(parsed)
            if not text:
                logger.warning("Gemini returned empty content")
                return GeminiDebugCallResult(
                    success=False,
                    result=None,
                    error="Gemini returned empty content.",
                    message="Gemini fallback call completed but no content was returned.",
                    raw_response_available=True,
                )

            structured = self._safe_json_parse(text)
            if not structured:
                logger.warning("Gemini returned non-JSON content")
                return GeminiDebugCallResult(
                    success=False,
                    result=None,
                    error="Gemini returned non-JSON content.",
                    message="Gemini fallback returned invalid JSON.",
                    raw_response_available=True,
                )

            validated = self._validate_response(structured)
            if not validated:
                logger.warning("Gemini response failed validation")
                return GeminiDebugCallResult(
                    success=False,
                    result=None,
                    error="Gemini response failed fixed-category validation.",
                    message="Gemini fallback returned a category outside the allowed list.",
                    raw_response_available=True,
                )

            return GeminiDebugCallResult(
                success=True,
                result=validated,
                error=None,
                message="Gemini fallback check completed successfully.",
                raw_response_available=True,
            )
        except error.HTTPError as exc:
            logger.warning("Gemini HTTP error: code=%s reason=%s", exc.code, exc.reason)
            return GeminiDebugCallResult(
                success=False,
                result=None,
                error=f"Gemini HTTP error {exc.code}: {exc.reason}",
                message="Gemini fallback API call failed.",
                raw_response_available=False,
            )
        except error.URLError as exc:
            logger.warning("Gemini network error: %s", exc.reason)
            return GeminiDebugCallResult(
                success=False,
                result=None,
                error=f"Gemini network error: {exc.reason}",
                message="Gemini fallback API call failed.",
                raw_response_available=False,
            )
        except TimeoutError:
            logger.warning("Gemini request timed out after %ss", self.timeout_seconds)
            return GeminiDebugCallResult(
                success=False,
                result=None,
                error=f"Gemini request timed out after {self.timeout_seconds}s.",
                message="Gemini fallback API call timed out.",
                raw_response_available=False,
            )
        except Exception:
            logger.exception("Unexpected Gemini fallback failure")
            return GeminiDebugCallResult(
                success=False,
                result=None,
                error="Unexpected Gemini fallback failure.",
                message="Gemini fallback API call failed.",
                raw_response_available=False,
            )

    def _build_prompt(
        self,
        title: str,
        description: str,
        brand: str | None,
        ml_top_candidates: list[dict[str, float | str]],
        very_low_confidence: bool,
        *,
        force_verify: bool,
        ml_prediction: str | None,
        ml_confidence: float | None,
        likely_wrong: bool,
    ) -> str:
        top_candidates_str = json.dumps(ml_top_candidates, ensure_ascii=True)
        categories_str = json.dumps(list(self.allowed_categories), ensure_ascii=True)
        ml_pred = ml_prediction or ""
        ml_conf = "" if ml_confidence is None else str(round(float(ml_confidence), 4))

        verify_block = ""
        if force_verify:
            verify_block = (
                "FORCE_VERIFY_MODE is true: you must independently decide the best final_category.\\n"
                "You may override the ML prediction if it is wrong for the product text.\\n"
            )
        elif likely_wrong:
            verify_block = (
                "LIKELY_WRONG_HINT is true: the ML label may contradict obvious product cues.\\n"
                "Choose the correct final_category from the text and ALLOWED_CATEGORIES.\\n"
            )

        return (
            "You are a strict product categorization assistant.\\n"
            "Choose exactly one final category from ALLOWED_CATEGORIES.\\n"
            "Never output markdown. Return valid JSON only.\\n"
            "Do not invent a new top-level category outside ALLOWED_CATEGORIES.\\n"
            "Prefer Fashion for apparel, lingerie, bras, footwear, handbags, and accessories.\\n"
            "Prefer Electronics for gadgets, chargers, adapters, cables, and devices.\\n"
            "Prefer Home & Furniture for shelves, tables, storage, and decor.\\n"
            "Prefer Health & Wellness for supplements and protein powders.\\n"
            "Prefer Beauty & Personal Care for cosmetics and skincare.\\n"
            "Prefer Automotive for car mounts and vehicle accessories.\\n"
            "\\n"
            f"{verify_block}"
            f"ALLOWED_CATEGORIES: {categories_str}\\n"
            f"PRODUCT_TITLE: {title}\\n"
            f"PRODUCT_DESCRIPTION: {description}\\n"
            f"PRODUCT_BRAND: {brand or ''}\\n"
            f"ML_TOP_CANDIDATES: {top_candidates_str}\\n"
            f"ML_PREDICTION: {ml_pred}\\n"
            f"ML_CONFIDENCE: {ml_conf}\\n"
            f"VERY_LOW_CONFIDENCE: {'true' if very_low_confidence else 'false'}\\n"
            f"LIKELY_WRONG_HINT: {'true' if likely_wrong else 'false'}\\n"
            f"FORCE_VERIFY_MODE: {'true' if force_verify else 'false'}\\n"
            "\\n"
            "Return JSON with this exact shape:\\n"
            "{\\n"
            '  "final_category": "Fashion",\\n'
            '  "suggested_new_category": "Women Innerwear > Bra",\\n'
            '  "reason": "short reason",\\n'
            '  "confidence": 0.94,\\n'
            '  "review_needed": false\\n'
            "}\\n"
            "\\n"
            "Rules:\\n"
            "1) final_category must be exactly one string from ALLOWED_CATEGORIES.\\n"
            "2) suggested_new_category may be null or a more specific sub-label (not a new top-level).\\n"
            "3) If VERY_LOW_CONFIDENCE is true, suggested_new_category can be more specific and user-friendly.\\n"
            "4) suggested_new_category must stay related to the chosen final_category.\\n"
        )

    def _extract_text(self, payload: dict[str, Any]) -> str | None:
        candidates = payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            return None

        first = candidates[0]
        if not isinstance(first, dict):
            return None

        content = first.get("content")
        if not isinstance(content, dict):
            return None

        parts = content.get("parts")
        if not isinstance(parts, list) or not parts:
            return None

        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                return part["text"].strip()

        return None

    def _safe_json_parse(self, text: str) -> dict[str, Any] | None:
        text = text.strip()

        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()

        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None

    def _validate_response(self, data: dict[str, Any]) -> GeminiFallbackResult | None:
        final_category_raw = str(data.get("final_category", "")).strip()
        if final_category_raw not in self.allowed_categories:
            return None

        suggested_raw = data.get("suggested_new_category")
        suggested_new_category: str | None = None
        if isinstance(suggested_raw, str):
            cleaned = suggested_raw.strip()
            suggested_new_category = cleaned or None

        reason = str(data.get("reason", "Gemini fallback used.")).strip() or "Gemini fallback used."

        confidence_raw = data.get("confidence", 0.0)
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        review_needed = bool(data.get("review_needed", False))

        return GeminiFallbackResult(
            final_category=final_category_raw,
            suggested_new_category=suggested_new_category,
            reason=reason,
            confidence=confidence,
            review_needed=review_needed,
        )
