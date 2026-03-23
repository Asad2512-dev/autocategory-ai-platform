import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class FeedbackStore:
    """
    Stores admin-corrected category feedback for future retraining.
    This class is intentionally simple and can be called by Laravel-backed
    correction flows later (via a dedicated endpoint or batch sync).
    """

    def __init__(self, feedback_dataset_path: Path) -> None:
        self.feedback_dataset_path = feedback_dataset_path

    def build_feedback_record(self, title: str, description: str, final_category: str) -> dict[str, str]:
        return {
            "title": title.strip(),
            "description": description.strip(),
            "category": final_category.strip(),
        }

    def append_feedback_record(self, record: dict[str, Any]) -> None:
        self.feedback_dataset_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = self.feedback_dataset_path.exists()

        with self.feedback_dataset_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["title", "description", "category"])
            if not file_exists:
                writer.writeheader()
            writer.writerow(
                {
                    "title": str(record.get("title", "")).strip(),
                    "description": str(record.get("description", "")).strip(),
                    "category": str(record.get("category", "")).strip(),
                }
            )

    def append_feedback_correction(self, record: dict[str, Any]) -> None:
        self.feedback_dataset_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = self.feedback_dataset_path.exists()

        fieldnames = [
            "timestamp",
            "title",
            "description",
            "predicted_category",
            "corrected_category",
            "confidence",
            "low_confidence",
            "review_needed",
            "flagged_for_retraining",
            "prediction_source",
        ]

        with self.feedback_dataset_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()

            writer.writerow(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "title": str(record.get("title", "")).strip(),
                    "description": str(record.get("description", "")).strip(),
                    "predicted_category": str(record.get("predicted_category", "")).strip(),
                    "corrected_category": str(record.get("corrected_category", "")).strip(),
                    "confidence": float(record.get("confidence", 0.0)),
                    "low_confidence": bool(record.get("low_confidence", False)),
                    "review_needed": bool(record.get("review_needed", False)),
                    "flagged_for_retraining": bool(record.get("flagged_for_retraining", False)),
                    "prediction_source": str(record.get("prediction_source", "")).strip(),
                }
            )
