import unittest

from app.services.category_resolver import CategoryResolver
from app.services.fallback_classifier import FallbackClassifier


KNOWN_CATEGORIES = (
    "Electronics",
    "Fashion",
    "Home & Furniture",
    "Beauty & Personal Care",
    "Books",
    "Sports & Outdoors",
    "Toys & Games",
    "Automotive",
    "Health & Wellness",
    "Grocery & Food",
)


class FallbackExamplesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fallback = FallbackClassifier(known_categories=KNOWN_CATEGORIES)
        self.resolver = CategoryResolver(known_categories=KNOWN_CATEGORIES)

    def _top_category(self, text: str) -> str:
        matches = self.fallback.classify(text)
        self.assertTrue(matches, f"Expected fallback matches for text: {text}")
        return matches[0].category

    def test_slim_bra_maps_to_fashion(self) -> None:
        self.assertEqual(self._top_category("Slim Bra for women"), "Fashion")

    def test_sports_bra_maps_to_fashion(self) -> None:
        self.assertEqual(self._top_category("Sports Bra padded fit"), "Fashion")

    def test_iphone_charger_maps_to_electronics(self) -> None:
        self.assertEqual(self._top_category("iPhone Charger fast charging cable"), "Electronics")

    def test_dining_table_maps_to_home_and_furniture(self) -> None:
        self.assertEqual(self._top_category("Wooden Dining Table 6 seater"), "Home & Furniture")

    def test_dining_wall_shelf_maps_to_home_and_furniture(self) -> None:
        self.assertEqual(self._top_category("Dining Wall Shelf wooden decor"), "Home & Furniture")

    def test_yoga_resistance_band_maps_to_sports_and_outdoors(self) -> None:
        self.assertEqual(self._top_category("Yoga Resistance Band set"), "Sports & Outdoors")

    def test_low_confidence_override_for_bra(self) -> None:
        override = self.resolver.resolve_low_confidence_override(
            model_category="Electronics",
            title="Slim Bra",
            description="comfortable innerwear lingerie",
            confidence=0.22,
            threshold=0.65,
        )
        self.assertIsNotNone(override)
        self.assertEqual(override.category, "Fashion")


if __name__ == "__main__":
    unittest.main()
