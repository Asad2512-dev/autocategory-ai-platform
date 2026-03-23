import os
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


@dataclass(frozen=True)
class Settings:
    project_dir: Path
    model_dir: Path
    model_confidence_threshold: float
    very_low_confidence_threshold: float
    known_categories: Tuple[str, ...]
    feedback_dataset_path: Path
    gemini_enabled: bool
    gemini_api_key: str
    gemini_model: str
    gemini_timeout_seconds: float
    gemini_force_verify: bool


def _get_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}



def get_settings() -> Settings:
    project_dir = Path(__file__).resolve().parents[2]
    model_dir_env = os.getenv("MODEL_DIR")
    model_confidence_threshold = float(
        os.getenv("MODEL_CONFIDENCE_THRESHOLD", os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
    )
    very_low_confidence_threshold = float(os.getenv("VERY_LOW_CONFIDENCE_THRESHOLD", "0.45"))
    gemini_enabled = _get_bool_env("GEMINI_ENABLED", default=False)
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    gemini_timeout_seconds = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "8"))
    gemini_force_verify = _get_bool_env("GEMINI_FORCE_VERIFY", default=False)

    known_categories = (
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

    feedback_dataset_env = os.getenv("FEEDBACK_DATASET_PATH")

    if model_dir_env:
        model_dir = Path(model_dir_env).expanduser().resolve()
    else:
        model_dir = (project_dir / "model").resolve()

    if feedback_dataset_env:
        feedback_dataset_path = Path(feedback_dataset_env).expanduser().resolve()
    else:
        feedback_dataset_path = (project_dir / "data" / "feedback_corrections.csv").resolve()

    return Settings(
        project_dir=project_dir,
        model_dir=model_dir,
        model_confidence_threshold=model_confidence_threshold,
        very_low_confidence_threshold=very_low_confidence_threshold,
        known_categories=known_categories,
        feedback_dataset_path=feedback_dataset_path,
        gemini_enabled=gemini_enabled,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        gemini_timeout_seconds=gemini_timeout_seconds,
        gemini_force_verify=gemini_force_verify,
    )


settings = get_settings()
