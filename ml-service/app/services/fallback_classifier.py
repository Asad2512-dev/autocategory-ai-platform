import re
from dataclasses import dataclass


@dataclass
class FallbackMatch:
    category: str
    score: float


class FallbackClassifier:
    def __init__(self, known_categories: tuple[str, ...]) -> None:
        self.known_categories = known_categories
        self.keyword_weights: dict[str, dict[str, float]] = {
            "Electronics": {
                "iphone": 2.6,
                "android": 2.0,
                "phone": 1.6,
                "mobile": 1.4,
                "laptop": 1.8,
                "camera": 1.6,
                "tv": 1.6,
                "headphone": 1.4,
                "charger": 2.4,
                "adapter": 1.8,
                "cable": 1.7,
                "usb": 1.2,
                "bluetooth": 1.4,
                "tablet": 1.4,
                "speaker": 1.3,
                "ssd": 1.2,
                "power bank": 1.8,
            },
            "Fashion": {
                "jeans": 1.6,
                "shirt": 1.2,
                "dress": 1.3,
                "jacket": 1.2,
                "shoe": 1.1,
                "sneaker": 1.2,
                "sandal": 1.1,
                "hoodie": 1.1,
                "skirt": 1.2,
                "blouse": 1.2,
                "fashion": 1.0,
                "bra": 4.2,
                "bralette": 4.0,
                "lingerie": 4.0,
                "innerwear": 3.8,
                "underwear": 3.6,
                "panties": 3.6,
                "shapewear": 3.6,
                "camisole": 3.4,
                "padded bra": 4.4,
                "sports bra": 4.4,
            },
            "Home & Furniture": {
                "sofa": 1.8,
                "table": 1.8,
                "chair": 1.6,
                "pillow": 1.3,
                "mattress": 1.6,
                "kitchen": 1.2,
                "furniture": 1.8,
                "shelf": 1.6,
                "wall shelf": 2.8,
                "home decor": 2.2,
                "vacuum": 1.3,
                "bed": 1.5,
                "drawer": 1.3,
                "home": 1.0,
                "dining table": 2.8,
            },
            "Beauty & Personal Care": {
                "serum": 1.8,
                "moisturizer": 1.6,
                "lipstick": 1.6,
                "shampoo": 1.5,
                "perfume": 1.6,
                "skincare": 1.7,
                "beauty": 1.2,
                "face": 1.0,
                "cream": 1.4,
                "hair": 1.0,
            },
            "Books": {
                "book": 1.8,
                "novel": 1.8,
                "author": 1.3,
                "story": 1.3,
                "guide": 1.2,
                "edition": 1.1,
                "paperback": 1.4,
                "hardcover": 1.4,
                "publication": 1.2,
                "chapter": 1.0,
            },
            "Sports & Outdoors": {
                "cricket": 1.8,
                "football": 1.8,
                "yoga": 1.6,
                "dumbbell": 1.8,
                "racket": 1.6,
                "gym": 1.5,
                "sports": 1.2,
                "outdoor": 1.2,
                "fitness": 1.4,
                "exercise": 1.4,
                "resistance band": 2.8,
                "resistance": 1.5,
                "band": 1.2,
            },
            "Toys & Games": {
                "toy": 1.6,
                "game": 1.5,
                "puzzle": 1.6,
                "doll": 1.7,
                "blocks": 1.4,
                "kids": 1.1,
                "play": 1.1,
                "action figure": 2.2,
                "board game": 2.0,
                "car toy": 2.0,
            },
            "Automotive": {
                "car": 1.4,
                "engine": 1.8,
                "tire": 1.7,
                "brake": 1.7,
                "automotive": 1.6,
                "vehicle": 1.3,
                "gps": 1.4,
                "motor": 1.4,
                "dashboard": 1.4,
                "oil": 1.2,
            },
            "Health & Wellness": {
                "vitamin": 1.8,
                "supplement": 1.8,
                "wellness": 1.5,
                "health": 1.4,
                "protein": 1.6,
                "immunity": 1.6,
                "meditation": 1.4,
                "care": 1.1,
                "relief": 1.3,
                "therapy": 1.3,
            },
            "Grocery & Food": {
                "snack": 1.6,
                "organic": 1.5,
                "grocery": 1.6,
                "food": 1.4,
                "beverage": 1.5,
                "drink": 1.4,
                "tea": 1.4,
                "coffee": 1.4,
                "spice": 1.3,
                "pack": 1.0,
            },
        }
        self.strong_indicator_map: dict[str, str] = {
            "bra": "Fashion",
            "bralette": "Fashion",
            "lingerie": "Fashion",
            "innerwear": "Fashion",
            "underwear": "Fashion",
            "panties": "Fashion",
            "shapewear": "Fashion",
            "camisole": "Fashion",
            "padded bra": "Fashion",
            "sports bra": "Fashion",
        }

    @staticmethod
    def tokenize(text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    @staticmethod
    def normalize_text(text: str) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", text.lower()))

    def detect_strong_indicator(self, text: str) -> str | None:
        normalized_text = self.normalize_text(text)

        for indicator, category in self.strong_indicator_map.items():
            if f" {indicator} " in f" {normalized_text} ":
                return category

        return None

    def classify(self, text: str) -> list[FallbackMatch]:
        normalized_text = self.normalize_text(text)
        tokens = self.tokenize(normalized_text)

        if not tokens:
            return []

        token_set = set(tokens)
        raw_scores: dict[str, float] = {}

        strong_category = self.detect_strong_indicator(normalized_text)
        if strong_category:
            raw_scores[strong_category] = raw_scores.get(strong_category, 0.0) + 6.0

        for category in self.known_categories:
            weighted_keywords = self.keyword_weights.get(category, {})
            score = 0.0

            for keyword, weight in weighted_keywords.items():
                if " " in keyword:
                    if f" {keyword} " in f" {normalized_text} ":
                        score += weight
                    continue

                if keyword in token_set:
                    score += weight
                    continue

                if any(token.startswith(keyword) for token in token_set):
                    score += weight * 0.6

            if score > 0:
                raw_scores[category] = round(score, 4)

        if not raw_scores:
            return []

        total = sum(raw_scores.values())
        if total <= 0:
            return []

        normalized: list[FallbackMatch] = []
        for category, value in raw_scores.items():
            normalized.append(FallbackMatch(category=category, score=round(value / total, 4)))

        normalized.sort(key=lambda x: x.score, reverse=True)
        return normalized
