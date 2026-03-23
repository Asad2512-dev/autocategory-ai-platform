from dataclasses import dataclass

from app.services.fallback_classifier import FallbackClassifier


@dataclass
class ResolvedCategory:
    category: str
    source: str
    message: str


class CategoryResolver:
    def __init__(self, known_categories: tuple[str, ...]) -> None:
        self.known_categories = known_categories
        self.normalization_map = {
            "beauty": "Beauty & Personal Care",
            "beauty and personal care": "Beauty & Personal Care",
            "home": "Home & Furniture",
            "home and furniture": "Home & Furniture",
            "home & kitchen": "Home & Furniture",
            "sports": "Sports & Outdoors",
            "sports and outdoors": "Sports & Outdoors",
            "toys": "Toys & Games",
            "toys and games": "Toys & Games",
        }
        self.fallback = FallbackClassifier(known_categories=known_categories)

    def _resolve_with_fallback(self, title: str, description: str) -> ResolvedCategory:
        text = f"{title} {description}".strip()
        fallback_matches = self.fallback.classify(text)

        if fallback_matches:
            return ResolvedCategory(
                category=fallback_matches[0].category,
                source="fallback",
                message="Model label was not usable, keyword fallback category applied.",
            )

        return ResolvedCategory(
            category=self.known_categories[0],
            source="fallback",
            message="No strong fallback match found, default category applied.",
        )

    def normalize(self, category_name: str | None) -> str | None:
        if not category_name:
            return None

        raw = " ".join(category_name.strip().split())
        if not raw:
            return None

        lowered = raw.lower()

        if raw in self.known_categories:
            return raw

        if lowered in self.normalization_map:
            return self.normalization_map[lowered]

        # Partial matching to known categories.
        for known in self.known_categories:
            if lowered in known.lower() or known.lower() in lowered:
                return known

        return None

    def resolve(
        self,
        model_category: str | None,
        title: str,
        description: str,
    ) -> ResolvedCategory:
        normalized = self.normalize(model_category)

        if normalized:
            return ResolvedCategory(
                category=normalized,
                source="model",
                message="Model category accepted.",
            )

        return self._resolve_with_fallback(title=title, description=description)

    def resolve_low_confidence_override(
        self,
        model_category: str,
        title: str,
        description: str,
        confidence: float,
        threshold: float,
    ) -> ResolvedCategory | None:
        if confidence >= threshold:
            return None

        text = f"{title} {description}".strip()
        strong_indicator_category = self.fallback.detect_strong_indicator(text)
        normalized_model = self.normalize(model_category) or model_category

        if strong_indicator_category and normalized_model != strong_indicator_category:
            return ResolvedCategory(
                category=strong_indicator_category,
                source="fallback",
                message="Low confidence with strong keyword indicator. Fallback override applied.",
            )

        fallback_matches = self.fallback.classify(text)
        if not fallback_matches:
            return None

        best_match = fallback_matches[0]
        if best_match.category == normalized_model:
            return None

        second_score = fallback_matches[1].score if len(fallback_matches) > 1 else 0.0
        strong_margin = best_match.score - second_score

        if best_match.score >= 0.5 and strong_margin >= 0.2:
            return ResolvedCategory(
                category=best_match.category,
                source="fallback",
                message="Low confidence model output. Strong keyword fallback override applied.",
            )

        return None

    # Future hook: admin-corrected categories can be appended to a feedback dataset
    # and used by the training pipeline for periodic retraining.
