"""
Heuristics: model category likely wrong vs obvious product text (keyword / domain mismatch).
Used to escalate to Gemini even when model probability looks superficially high.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.fallback_classifier import FallbackClassifier

# (tuple of substrings to find in normalized text, forbidden model categories for that signal)
_HARD_MISMATCHES: tuple[tuple[tuple[str, ...], frozenset[str]], ...] = (
    (
        ("bra", "bralette", "lingerie", "sports bra", "strap bra", "slim bra", "padded bra"),
        frozenset(
            {
                "Electronics",
                "Books",
                "Toys & Games",
                "Automotive",
                "Grocery & Food",
                "Home & Furniture",
            }
        ),
    ),
    (
        ("charger", "charging cable", "usb-c", "usb c", "lightning cable", "power adapter", "wall adapter"),
        frozenset({"Fashion", "Beauty & Personal Care", "Books", "Toys & Games", "Grocery & Food"}),
    ),
    (
        ("wall shelf", "floating shelf", "dining table", "kitchen shelf", "bookshelf"),
        frozenset({"Beauty & Personal Care", "Books", "Toys & Games", "Fashion", "Health & Wellness"}),
    ),
    (
        ("protein powder", "whey protein", "casein", "mass gainer"),
        frozenset({"Toys & Games", "Books", "Electronics", "Fashion", "Automotive"}),
    ),
    (
        ("lipstick", "lip gloss", "mascara", "foundation", "eyeshadow", "concealer"),
        frozenset({"Electronics", "Automotive", "Toys & Games", "Books", "Sports & Outdoors"}),
    ),
    (
        ("car mount", "phone mount", "dashboard mount", "vent mount", "magnetic mount"),
        frozenset({"Fashion", "Beauty & Personal Care", "Books", "Toys & Games", "Grocery & Food"}),
    ),
    (
        ("kitchen knife", "knife set", "chef knife", "paring knife"),
        frozenset({"Beauty & Personal Care", "Electronics", "Fashion", "Books", "Toys & Games"}),
    ),
)


def _hard_mismatch(normalized_text: str, model_category: str) -> bool:
    blob = f" {normalized_text} "
    for phrases, forbidden in _HARD_MISMATCHES:
        if model_category not in forbidden:
            continue
        for p in phrases:
            if p in blob:
                return True
    return False


def is_likely_wrong_prediction(
    processed_text: str,
    model_category: str,
    model_confidence: float,
    classifier: FallbackClassifier,
) -> bool:
    """
    True if we should not trust the model label alone (escalate to keyword/Gemini path).
    """
    strong = classifier.detect_strong_indicator(processed_text)
    if strong and strong != model_category:
        return True

    if _hard_mismatch(processed_text, model_category):
        return True

    matches = classifier.classify(processed_text)
    if not matches:
        return False

    top = matches[0]
    if top.category == model_category:
        return False

    # Top keyword category disagrees with model
    if top.score >= 0.48:
        return True
    if top.score >= 0.35 and model_confidence < 0.88:
        return True

    return False
