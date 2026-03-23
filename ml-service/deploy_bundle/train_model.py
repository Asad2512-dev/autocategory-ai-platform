import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GridSearchCV, KFold, StratifiedKFold, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RAW_DATASETS = [
    "training_dataset.csv",
    "training_dataset2.csv",
    "training_dataset3.csv",
]
DEFAULT_CLEANED_CANDIDATES = {
    "training_dataset.csv": ["training_dataset.cleaned.csv"],
    "training_dataset2.csv": ["training_dataset2.cleaned.csv"],
    "training_dataset3.csv": ["training_dataset3.cleaned.csv"],
}

FINAL_CATEGORIES = {
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
}

CATEGORY_ALIASES = {
    "electronics": "Electronics",
    "electronic": "Electronics",
    "mobile": "Electronics",
    "charger": "Electronics",
    "gadgets": "Electronics",
    "laptop accessories": "Electronics",
    "phone accessories": "Electronics",
    "fashion": "Fashion",
    "clothing": "Fashion",
    "apparel": "Fashion",
    "bra": "Fashion",
    "lingerie": "Fashion",
    "underwear": "Fashion",
    "footwear": "Fashion",
    "handbags": "Fashion",
    "home": "Home & Furniture",
    "furniture": "Home & Furniture",
    "decor": "Home & Furniture",
    "kitchen": "Home & Furniture",
    "bedding": "Home & Furniture",
    "beauty": "Beauty & Personal Care",
    "skincare": "Beauty & Personal Care",
    "makeup": "Beauty & Personal Care",
    "haircare": "Beauty & Personal Care",
    "personal care": "Beauty & Personal Care",
    "books": "Books",
    "book": "Books",
    "novel": "Books",
    "textbook": "Books",
    "children books": "Books",
    "sports": "Sports & Outdoors",
    "gym": "Sports & Outdoors",
    "cricket": "Sports & Outdoors",
    "football": "Sports & Outdoors",
    "cycling": "Sports & Outdoors",
    "outdoors": "Sports & Outdoors",
    "toys": "Toys & Games",
    "toy": "Toys & Games",
    "dolls": "Toys & Games",
    "puzzles": "Toys & Games",
    "games": "Toys & Games",
    "automotive": "Automotive",
    "car accessories": "Automotive",
    "bike accessories": "Automotive",
    "health": "Health & Wellness",
    "supplements": "Health & Wellness",
    "personal health": "Health & Wellness",
    "wellness": "Health & Wellness",
    "grocery": "Grocery & Food",
    "food": "Grocery & Food",
    "beverages": "Grocery & Food",
    "snacks": "Grocery & Food",
}

COLUMN_ALIASES = {
    "title": ["title", "product_title", "name", "product_name"],
    "description": ["description", "details", "desc", "product_description"],
    "category": ["category", "label", "class", "target"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train product categorization model from one or more CSV datasets."
    )
    parser.add_argument(
        "--data",
        action="append",
        default=None,
        help=(
            "Path to input CSV. Pass multiple times for multiple files. "
            "If omitted, defaults are auto-detected."
        ),
    )
    parser.add_argument(
        "--export-cleaned",
        action="store_true",
        help="Export merged cleaned dataset to cleaned output path.",
    )
    parser.add_argument(
        "--cleaned-output",
        default="data/final_merged_cleaned_dataset.csv",
        help="Output path for cleaned merged dataset.",
    )
    parser.add_argument(
        "--model-dir",
        default="model",
        help="Directory where final model artifacts are saved.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test split ratio. Default is 0.2.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility. Default is 42.",
    )
    parser.add_argument(
        "--show-top-features",
        action="store_true",
        help="Print top 15 positive terms per class for best linear model.",
    )
    parser.add_argument(
        "--semi-supervised",
        action="store_true",
        help="Run pseudo-label self-training benchmark and write semi_supervised_metrics.json.",
    )
    parser.add_argument(
        "--pseudo-confidence",
        type=float,
        default=0.92,
        help="Min max-probability for accepting pseudo-labels (default: 0.92).",
    )
    parser.add_argument(
        "--report-dir",
        default="",
        help=(
            "Directory for model_comparison.csv, metrics.json, and semi_supervised_metrics.json "
            "(default: same as --model-dir)."
        ),
    )
    return parser.parse_args()


def preprocess_text(text: Any) -> str:
    value = str(text).lower().strip()
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_category(category: Any) -> str:
    raw = preprocess_text(category)
    if not raw:
        return ""

    for final_label in FINAL_CATEGORIES:
        if raw == preprocess_text(final_label):
            return final_label

    if raw in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[raw]

    for alias, mapped in CATEGORY_ALIASES.items():
        if alias in raw:
            return mapped

    return ""


def _resolve_existing_path(raw_path: str) -> Path | None:
    candidate = Path(raw_path)
    if candidate.exists():
        return candidate.resolve()

    candidate_base = (BASE_DIR / raw_path)
    if candidate_base.exists():
        return candidate_base.resolve()

    candidate_data = (BASE_DIR / "data" / raw_path)
    if candidate_data.exists():
        return candidate_data.resolve()

    return None


def resolve_dataset_paths(user_paths: list[str] | None) -> list[Path]:
    resolved: list[Path] = []

    if user_paths:
        expanded_paths: list[str] = []
        for raw_item in user_paths:
            parts = [part.strip() for part in str(raw_item).split(",") if part.strip()]
            expanded_paths.extend(parts)

        for path_str in expanded_paths:
            resolved_path = _resolve_existing_path(path_str)
            if resolved_path is not None:
                resolved.append(resolved_path)
            else:
                print(f"Warning: Dataset path not found and skipped: {path_str}")
        return resolved

    for default_raw in DEFAULT_RAW_DATASETS:
        raw_path = _resolve_existing_path(default_raw)
        if raw_path is not None:
            resolved.append(raw_path)
            continue

        cleaned_fallbacks = DEFAULT_CLEANED_CANDIDATES.get(default_raw, [])
        used_fallback = False
        for fallback_name in cleaned_fallbacks:
            fallback_path = _resolve_existing_path(fallback_name)
            if fallback_path is not None:
                resolved.append(fallback_path)
                used_fallback = True
                print(
                    "Warning: Raw file missing; using cleaned fallback for "
                    f"{default_raw}: {fallback_path.name}"
                )
                break

        if not used_fallback:
            print(f"Warning: Default dataset not found and skipped: {default_raw}")

    return resolved


def _standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    renamed = df.copy()
    renamed.columns = [str(col).strip() for col in renamed.columns]

    normalized_lookup = {
        str(col).strip().lower().replace(" ", "_"): col for col in renamed.columns
    }

    selected_columns: dict[str, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        found = None
        for alias in aliases:
            key = alias.strip().lower().replace(" ", "_")
            if key in normalized_lookup:
                found = normalized_lookup[key]
                break

        if found is None:
            raise ValueError(
                "Could not resolve required field "
                f"'{canonical}'. Available columns: {list(renamed.columns)}"
            )

        selected_columns[canonical] = found

    standardized = renamed[
        [selected_columns["title"], selected_columns["description"], selected_columns["category"]]
    ].copy()
    standardized.columns = ["title", "description", "category"]
    return standardized


def load_and_merge_datasets(paths: list[Path]) -> pd.DataFrame:
    if not paths:
        raise FileNotFoundError(
            "No dataset files found. Provide --data paths or place default datasets in project."
        )

    frames: list[pd.DataFrame] = []
    print("\n=== Dataset Loading ===")

    for path in paths:
        df = pd.read_csv(path)
        standardized = _standardize_column_names(df)
        standardized["source_file"] = path.name
        frames.append(standardized)
        print(f"- Loaded {path}: {len(standardized)} rows")

    merged = pd.concat(frames, ignore_index=True)
    print(f"Total rows after merge: {len(merged)}")
    return merged


def warn_cross_file_duplicates(df: pd.DataFrame) -> None:
    key_df = df[["cleaned_text", "category", "source_file"]].copy()
    grouped = key_df.groupby(["cleaned_text", "category"])["source_file"].nunique()
    cross_file_dupes = int((grouped > 1).sum())

    if cross_file_dupes > 0:
        print(
            "Warning: Potential cross-file duplicate leakage detected. "
            f"Duplicate text/category groups across files: {cross_file_dupes}"
        )


def print_category_distribution(df: pd.DataFrame) -> None:
    distribution = df["category"].value_counts().sort_index()
    print("\n=== Category Distribution (After Normalization) ===")
    for category, count in distribution.items():
        print(f"- {category}: {count}")


def print_dataset_quality_snapshot(raw_rows: int, cleaned: pd.DataFrame) -> None:
    print("\n=== Dataset Quality Snapshot ===")
    print(f"Rows before cleaning: {raw_rows}")
    print(f"Rows after cleaning:  {len(cleaned)}")
    print(f"Unique categories:    {cleaned['category'].nunique()}")
    print_category_distribution(cleaned)

    counts = cleaned["category"].value_counts()
    low_classes = counts[counts < 5]
    if not low_classes.empty:
        print("Warning: Low-sample categories detected (<5 rows):")
        for category, count in low_classes.sort_values().items():
            print(f"- {category}: {int(count)}")

    print("\nExample cleaned rows:")
    preview_cols = ["title", "description", "category", "source_file"]
    print(cleaned[preview_cols].head(5).to_string(index=False))


def prepare_clean_dataset(merged_df: pd.DataFrame) -> pd.DataFrame:
    cleaned = merged_df.copy()

    cleaned = cleaned.dropna(subset=["title", "description", "category"]).copy()
    cleaned.loc[:, "title"] = cleaned["title"].astype(str).map(preprocess_text)
    cleaned.loc[:, "description"] = cleaned["description"].astype(str).map(preprocess_text)
    cleaned.loc[:, "category"] = cleaned["category"].astype(str).map(normalize_category)

    cleaned = cleaned[(cleaned["title"].str.len() >= 2) & (cleaned["description"].str.len() >= 2)]
    cleaned = cleaned[cleaned["category"].isin(FINAL_CATEGORIES)].copy()

    cleaned.loc[:, "cleaned_text"] = (
        cleaned["title"].str.strip() + " " + cleaned["description"].str.strip()
    ).str.strip()
    cleaned = cleaned[cleaned["cleaned_text"].str.len() >= 8].copy()

    before_exact = len(cleaned)
    cleaned = cleaned.drop_duplicates(subset=["title", "description", "category"]).copy()
    exact_removed = before_exact - len(cleaned)
    if exact_removed > 0:
        print(f"Removed exact duplicate rows: {exact_removed}")

    before_text_cat = len(cleaned)
    cleaned = cleaned.drop_duplicates(subset=["cleaned_text", "category"]).copy()
    text_cat_removed = before_text_cat - len(cleaned)
    if text_cat_removed > 0:
        print(f"Removed duplicate cleaned_text/category rows: {text_cat_removed}")

    warn_cross_file_duplicates(cleaned)
    return cleaned


def build_cv_strategy(y_train: Any, random_state: int) -> Any:
    label_counts = pd.Series(y_train).value_counts()
    min_count = int(label_counts.min()) if not label_counts.empty else 0

    if min_count >= 2:
        n_splits = min(5, min_count)
        return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    print("Warning: Not enough samples per class for stratified CV. Using KFold CV.")
    return KFold(n_splits=3, shuffle=True, random_state=random_state)


def build_model(model_name: str, random_state: int) -> Any:
    if model_name == "LogisticRegression":
        return LogisticRegression(max_iter=1000, random_state=random_state)
    if model_name == "LinearSVC":
        return LinearSVC(random_state=random_state)
    if model_name == "MultinomialNB":
        return MultinomialNB()
    if model_name == "RandomForest":
        return RandomForestClassifier(
            random_state=random_state,
            n_jobs=-1,
            class_weight="balanced_subsample",
        )
    raise ValueError(f"Unsupported model: {model_name}")


def supports_predict_proba(model: Any) -> bool:
    return callable(getattr(model, "predict_proba", None))


def supports_decision_function(model: Any) -> bool:
    return callable(getattr(model, "decision_function", None))


def evaluate_baseline_configs(
    x_train: list[str],
    x_test: list[str],
    y_train: Any,
    y_test: Any,
    random_state: int,
) -> pd.DataFrame:
    model_families = ["LogisticRegression", "LinearSVC", "MultinomialNB", "RandomForest"]
    ngram_configs = [(1, 1), (1, 2)]

    rows: list[dict[str, Any]] = []
    for model_name in model_families:
        for ngram_range in ngram_configs:
            pipeline = Pipeline(
                [
                    (
                        "tfidf",
                        TfidfVectorizer(
                            max_features=10000,
                            ngram_range=ngram_range,
                        ),
                    ),
                    ("model", build_model(model_name=model_name, random_state=random_state)),
                ]
            )
            pipeline.fit(x_train, y_train)
            train_pred = pipeline.predict(x_train)
            test_pred = pipeline.predict(x_test)

            rows.append(
                {
                    "model_name": model_name,
                    "ngram_range": str(ngram_range),
                    "train_accuracy": accuracy_score(y_train, train_pred),
                    "test_accuracy": accuracy_score(y_test, test_pred),
                    "weighted_precision": precision_score(
                        y_test, test_pred, average="weighted", zero_division=0
                    ),
                    "weighted_recall": recall_score(
                        y_test, test_pred, average="weighted", zero_division=0
                    ),
                    "weighted_f1": f1_score(
                        y_test, test_pred, average="weighted", zero_division=0
                    ),
                }
            )

    result_df = pd.DataFrame(rows).sort_values(by="weighted_f1", ascending=False)
    print("\n=== Baseline Model Comparison (Sorted by weighted_f1) ===")
    print(result_df.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    return result_df


def build_param_grid(model_name: str) -> dict[str, list[Any]]:
    grid: dict[str, list[Any]] = {
        "tfidf__ngram_range": [(1, 1), (1, 2)],
        "tfidf__min_df": [1, 2, 3],
        "tfidf__sublinear_tf": [True, False],
    }

    if model_name == "LogisticRegression":
        grid.update(
            {
                "model__C": [0.5, 1.0, 2.0, 5.0],
                "model__class_weight": [None, "balanced"],
                "model__max_iter": [1000, 2000],
            }
        )
        return grid

    if model_name == "LinearSVC":
        grid.update(
            {
                "model__C": [0.5, 1.0, 2.0, 5.0],
                "model__class_weight": [None, "balanced"],
            }
        )
        return grid

    if model_name == "MultinomialNB":
        grid.update(
            {
                "model__alpha": [0.1, 0.5, 1.0],
            }
        )
        return grid

    if model_name == "RandomForest":
        grid.update(
            {
                "model__n_estimators": [100, 200],
                "model__max_depth": [None, 40],
                "model__min_samples_leaf": [1, 2],
            }
        )
        return grid

    raise ValueError(f"Unsupported model for grid: {model_name}")


def tune_model_family(
    model_name: str,
    x_train: list[str],
    x_test: list[str],
    y_train: Any,
    y_test: Any,
    random_state: int,
) -> dict[str, Any]:
    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=10000)),
            ("model", build_model(model_name=model_name, random_state=random_state)),
        ]
    )

    search = GridSearchCV(
        estimator=pipeline,
        param_grid=build_param_grid(model_name),
        scoring="f1_weighted",
        cv=build_cv_strategy(y_train=y_train, random_state=random_state),
        n_jobs=1,
        refit=True,
        verbose=0,
    )
    search.fit(x_train, y_train)

    best_pipeline = search.best_estimator_
    train_pred = best_pipeline.predict(x_train)
    test_pred = best_pipeline.predict(x_test)

    model_obj = best_pipeline.named_steps["model"]
    return {
        "model_name": model_name,
        "best_params": search.best_params_,
        "best_cv_f1": float(search.best_score_),
        "train_accuracy": accuracy_score(y_train, train_pred),
        "test_accuracy": accuracy_score(y_test, test_pred),
        "weighted_precision": precision_score(y_test, test_pred, average="weighted", zero_division=0),
        "weighted_recall": recall_score(y_test, test_pred, average="weighted", zero_division=0),
        "weighted_f1": f1_score(y_test, test_pred, average="weighted", zero_division=0),
        "supports_predict_proba": supports_predict_proba(model_obj),
        "supports_decision_function": supports_decision_function(model_obj),
        "pipeline": best_pipeline,
        "test_pred": test_pred,
    }


def print_tuning_summary(results: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for result in results:
        rows.append(
            {
                "model_name": result["model_name"],
                "ngram_range": str(result["best_params"].get("tfidf__ngram_range", "N/A")),
                "train_accuracy": result["train_accuracy"],
                "test_accuracy": result["test_accuracy"],
                "weighted_precision": result["weighted_precision"],
                "weighted_recall": result["weighted_recall"],
                "weighted_f1": result["weighted_f1"],
                "best_cv_f1": result["best_cv_f1"],
                "supports_predict_proba": bool(result["supports_predict_proba"]),
            }
        )

    df = pd.DataFrame(rows).sort_values(
        by=["weighted_f1", "supports_predict_proba", "best_cv_f1"],
        ascending=[False, False, False],
    )

    print("\n=== Tuned Model Summary (Sorted by weighted_f1) ===")
    print(
        df[
            [
                "model_name",
                "ngram_range",
                "train_accuracy",
                "test_accuracy",
                "weighted_precision",
                "weighted_recall",
                "weighted_f1",
            ]
        ].to_string(index=False, float_format=lambda v: f"{v:.4f}")
    )
    return df


def print_per_class_f1(y_true: Any, y_pred: Any, label_encoder: LabelEncoder) -> None:
    labels = list(range(len(label_encoder.classes_)))
    _, _, f1_scores, supports = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
    )

    rows: list[dict[str, Any]] = []
    for idx, category in enumerate(label_encoder.classes_):
        rows.append(
            {
                "category": str(category),
                "f1": float(f1_scores[idx]),
                "support": int(supports[idx]),
            }
        )

    f1_df = pd.DataFrame(rows).sort_values(by="f1", ascending=False)
    print("\n=== Per-Class F1 ===")
    print(f1_df.to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    weakest = f1_df.sort_values(by="f1", ascending=True).head(min(3, len(f1_df)))
    print("\nWeakest categories:")
    for _, row in weakest.iterrows():
        print(f"- {row['category']}: F1={row['f1']:.4f}, support={int(row['support'])}")


def print_confusion_matrix_table(y_true: Any, y_pred: Any, label_encoder: LabelEncoder) -> pd.DataFrame:
    label_ids = list(range(len(label_encoder.classes_)))
    matrix = confusion_matrix(y_true, y_pred, labels=label_ids)
    class_names = [str(name) for name in label_encoder.classes_]

    matrix_df = pd.DataFrame(matrix, index=class_names, columns=class_names)
    print("\n=== Confusion Matrix (Best Model) ===")
    print("Rows=true, Columns=predicted")
    print(matrix_df.to_string())
    return matrix_df


def print_most_confused_pairs(matrix_df: pd.DataFrame, top_n: int = 10) -> None:
    rows: list[dict[str, Any]] = []
    for true_category in matrix_df.index:
        for predicted_category in matrix_df.columns:
            if true_category == predicted_category:
                continue
            count = int(matrix_df.loc[true_category, predicted_category])
            if count > 0:
                rows.append(
                    {
                        "true_category": str(true_category),
                        "predicted_category": str(predicted_category),
                        "count": count,
                    }
                )

    print("\n=== Most Confused Category Pairs ===")
    if not rows:
        print("No confused pairs found.")
        return

    confused_df = pd.DataFrame(rows).sort_values(by="count", ascending=False)
    print(confused_df.head(top_n).to_string(index=False))


def build_misclassified_examples(
    x_test: list[str],
    y_true: Any,
    y_pred: Any,
    label_encoder: LabelEncoder,
) -> pd.DataFrame:
    true_labels = [str(label_encoder.inverse_transform([int(v)])[0]) for v in y_true]
    pred_labels = [str(label_encoder.inverse_transform([int(v)])[0]) for v in y_pred]

    rows: list[dict[str, str]] = []
    for cleaned_text, true_category, predicted_category in zip(x_test, true_labels, pred_labels):
        if true_category != predicted_category:
            rows.append(
                {
                    "cleaned_text": str(cleaned_text),
                    "true_category": true_category,
                    "predicted_category": predicted_category,
                }
            )

    return pd.DataFrame(rows, columns=["cleaned_text", "true_category", "predicted_category"])


def print_targeted_mistakes(misclassified_df: pd.DataFrame) -> None:
    print("\n=== Targeted Mistake Checks ===")
    checks = [
        {
            "label": "bra predicted as Electronics",
            "keyword": "bra",
            "true_category": "Fashion",
            "predicted_category": "Electronics",
        },
        {
            "label": "charger predicted as Fashion",
            "keyword": "charger",
            "true_category": "Electronics",
            "predicted_category": "Fashion",
        },
    ]

    if misclassified_df.empty:
        print("No misclassified examples found.")
        return

    for check in checks:
        pattern = rf"\b{re.escape(str(check['keyword']))}\b"
        strict = misclassified_df[
            misclassified_df["cleaned_text"].str.contains(pattern, case=False, regex=True, na=False)
            & (misclassified_df["true_category"] == check["true_category"])
            & (misclassified_df["predicted_category"] == check["predicted_category"])
        ]

        print(f"- {check['label']}: {len(strict)}")
        if not strict.empty:
            print(strict.head(5).to_string(index=False))


def print_top_linear_features_per_class(
    pipeline: Pipeline,
    label_encoder: LabelEncoder,
    top_n: int = 15,
) -> None:
    model = pipeline.named_steps.get("model")
    vectorizer = pipeline.named_steps.get("tfidf")

    if model is None or vectorizer is None:
        print("\nInterpretability skipped: missing model/vectorizer.")
        return

    if model.__class__.__name__ not in {"LogisticRegression", "LinearSVC"}:
        print("\nInterpretability skipped: best model is not linear.")
        return

    coef = getattr(model, "coef_", None)
    if coef is None:
        print("\nInterpretability skipped: model has no coefficients.")
        return

    feature_names = vectorizer.get_feature_names_out()
    if len(feature_names) == 0:
        print("\nInterpretability skipped: vectorizer has empty vocabulary.")
        return

    print("\n=== Top Features Per Class (Best Linear Model) ===")
    coef_rows = coef
    class_names = [str(c) for c in label_encoder.classes_]

    if coef.shape[0] == 1 and len(class_names) == 2:
        coef_rows = [-coef[0], coef[0]]

    for class_idx, class_name in enumerate(class_names):
        if class_idx >= len(coef_rows):
            continue

        class_coef = coef_rows[class_idx]
        top_indices = class_coef.argsort()[::-1][:top_n]
        print(f"\n[{class_name}]")
        for rank, idx in enumerate(top_indices, start=1):
            print(f"{rank:>2}. {feature_names[int(idx)]:<30} weight={float(class_coef[int(idx)]):.4f}")


def save_artifacts(
    model_dir: Path,
    pipeline: Pipeline,
    label_encoder: LabelEncoder,
) -> tuple[Path, Path, Path]:
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / "model.pkl"
    vectorizer_path = model_dir / "vectorizer.pkl"
    label_encoder_path = model_dir / "label_encoder.pkl"

    joblib.dump(pipeline.named_steps["model"], model_path)
    joblib.dump(pipeline.named_steps["tfidf"], vectorizer_path)
    joblib.dump(label_encoder, label_encoder_path)

    return model_path, vectorizer_path, label_encoder_path


def _softmax_2d(logits: np.ndarray) -> np.ndarray:
    arr = np.asarray(logits, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    shifted = arr - np.max(arr, axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.sum(exp, axis=1, keepdims=True)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def classification_metrics_vector(y_true: Any, y_pred: Any) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


def save_comparison_and_metrics(
    reporting_dir: Path,
    tuned_results: list[dict[str, Any]],
    best_result: dict[str, Any],
    test_size: float,
    random_state: int,
) -> None:
    reporting_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for result in tuned_results:
        rows.append(
            {
                "model_name": result["model_name"],
                "accuracy": float(result["test_accuracy"]),
                "precision": float(result["weighted_precision"]),
                "recall": float(result["weighted_recall"]),
                "f1_score": float(result["weighted_f1"]),
                "train_accuracy": float(result["train_accuracy"]),
                "best_cv_f1_weighted": float(result["best_cv_f1"]),
                "supports_predict_proba": bool(result["supports_predict_proba"]),
            }
        )
    comparison_df = pd.DataFrame(rows).sort_values("f1_score", ascending=False)
    comparison_df.to_csv(reporting_dir / "model_comparison.csv", index=False)
    payload = {
        "test_size": test_size,
        "random_state": random_state,
        "best_model": best_result["model_name"],
        "models": rows,
    }
    (reporting_dir / "metrics.json").write_text(
        json.dumps(_json_safe(payload), indent=2),
        encoding="utf-8",
    )


def write_model_info_file(
    model_dir: Path,
    best_result: dict[str, Any],
    label_encoder: LabelEncoder,
    loaded_file_names: list[str],
    cleaned_rows: int,
) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    info = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fastapi_app_version": "1.0.0",
        "best_classifier": best_result["model_name"],
        "best_params": _json_safe(best_result["best_params"]),
        "num_labels": int(len(label_encoder.classes_)),
        "labels": [str(c) for c in label_encoder.classes_],
        "dataset_files": loaded_file_names,
        "cleaned_row_count": cleaned_rows,
        "test_metrics": {
            "accuracy": float(best_result["test_accuracy"]),
            "precision": float(best_result["weighted_precision"]),
            "recall": float(best_result["weighted_recall"]),
            "f1_score": float(best_result["weighted_f1"]),
        },
    }
    (model_dir / "model_info.json").write_text(
        json.dumps(info, indent=2),
        encoding="utf-8",
    )
    (model_dir / "class_labels.json").write_text(
        json.dumps([str(c) for c in label_encoder.classes_], indent=2),
        encoding="utf-8",
    )


def run_semi_supervised_self_training(
    x_train: list[str],
    y_train: np.ndarray,
    x_test: list[str],
    y_test: np.ndarray,
    label_encoder: LabelEncoder,
    best_pipeline_template: Any,
    random_state: int,
    confidence_threshold: float,
) -> dict[str, Any]:
    """Pseudo-label a held-out slice of the training set and measure test impact."""
    rng = np.random.default_rng(random_state)
    order = rng.permutation(len(x_train))
    split = max(1, int(0.65 * len(order)))
    lab_idx = order[:split]
    unl_idx = order[split:]

    x_lab = [x_train[int(i)] for i in lab_idx]
    y_lab = y_train[lab_idx]
    x_unl = [x_train[int(i)] for i in unl_idx]

    pipe_subset = clone(best_pipeline_template)
    pipe_subset.fit(x_lab, y_lab)
    pred_test_subset = pipe_subset.predict(x_test)
    metrics_subset = classification_metrics_vector(y_test, pred_test_subset)

    if not x_unl:
        return {
            "confidence_threshold": confidence_threshold,
            "labeled_only_size": len(x_lab),
            "unlabeled_pool_size": 0,
            "pseudo_accepted": 0,
            "metrics_before_pseudo": metrics_subset,
            "metrics_after_pseudo": metrics_subset,
            "note": "No unlabeled pool; skipped pseudo-labeling.",
        }

    tfidf = pipe_subset.named_steps["tfidf"]
    clf = pipe_subset.named_steps["model"]
    x_unl_matrix = tfidf.transform(x_unl)

    if hasattr(clf, "predict_proba"):
        proba = clf.predict_proba(x_unl_matrix)
    elif hasattr(clf, "decision_function"):
        proba = _softmax_2d(clf.decision_function(x_unl_matrix))
    else:
        return {
            "error": "Classifier has neither predict_proba nor decision_function; cannot pseudo-label.",
            "metrics_before_pseudo": metrics_subset,
        }

    conf = np.max(proba, axis=1)
    pseudo_y = np.argmax(proba, axis=1)
    accept = conf >= confidence_threshold
    n_accepted = int(np.sum(accept))
    if n_accepted == 0:
        metrics_after = metrics_subset
        x_aug = list(x_lab)
        y_aug = np.array(y_lab, copy=True)
    else:
        x_pseudo = [x_unl[i] for i in range(len(x_unl)) if accept[i]]
        y_pseudo = pseudo_y[accept]
        x_aug = x_lab + x_pseudo
        y_aug = np.concatenate([y_lab, y_pseudo])

    pipe_aug = clone(best_pipeline_template)
    pipe_aug.fit(x_aug, y_aug)
    pred_test_aug = pipe_aug.predict(x_test)
    metrics_after = classification_metrics_vector(y_test, pred_test_aug)

    return {
        "confidence_threshold": confidence_threshold,
        "labeled_only_size": len(x_lab),
        "unlabeled_pool_size": len(x_unl),
        "pseudo_accepted": n_accepted,
        "metrics_before_pseudo": metrics_subset,
        "metrics_after_pseudo": metrics_after,
    }


def save_training_summary(
    output_path: Path,
    loaded_files: list[str],
    cleaned_rows: int,
    best_result: dict[str, Any],
) -> None:
    summary = {
        "loaded_files": loaded_files,
        "total_cleaned_rows": cleaned_rows,
        "final_categories": sorted(FINAL_CATEGORIES),
        "best_model": best_result["model_name"],
        "best_params": best_result["best_params"],
        "final_metrics": {
            "train_accuracy": best_result["train_accuracy"],
            "test_accuracy": best_result["test_accuracy"],
            "weighted_precision": best_result["weighted_precision"],
            "weighted_recall": best_result["weighted_recall"],
            "weighted_f1": best_result["weighted_f1"],
            "best_cv_f1": best_result["best_cv_f1"],
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(_json_safe(summary), indent=2),
        encoding="utf-8",
    )


def train_pipeline(args: argparse.Namespace) -> None:
    dataset_paths = resolve_dataset_paths(args.data)
    merged = load_and_merge_datasets(dataset_paths)

    raw_rows = len(merged)
    cleaned = prepare_clean_dataset(merged)
    if cleaned.empty:
        raise ValueError("No training rows left after cleaning and category normalization.")

    print_dataset_quality_snapshot(raw_rows=raw_rows, cleaned=cleaned)

    if args.export_cleaned:
        cleaned_output = _resolve_existing_path(args.cleaned_output)
        cleaned_output = cleaned_output if cleaned_output is not None else Path(args.cleaned_output)
        if not cleaned_output.is_absolute():
            cleaned_output = (BASE_DIR / cleaned_output).resolve()
        cleaned_output.parent.mkdir(parents=True, exist_ok=True)
        cleaned.to_csv(cleaned_output, index=False)
        print(f"\nExported cleaned merged dataset: {cleaned_output}")

    texts = cleaned["cleaned_text"].tolist()
    labels = cleaned["category"].tolist()

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(labels)

    stratify_labels = y_encoded if (pd.Series(y_encoded).value_counts() >= 2).all() else None
    if stratify_labels is None:
        print(
            "Warning: At least one class has fewer than 2 samples; using non-stratified split."
        )

    x_train, x_test, y_train, y_test = train_test_split(
        texts,
        y_encoded,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=stratify_labels,
    )

    print("\n=== Train/Test Split ===")
    print(f"Train size: {len(x_train)}")
    print(f"Test size:  {len(x_test)}")

    train_labels = [str(label_encoder.inverse_transform([v])[0]) for v in y_train]
    test_labels = [str(label_encoder.inverse_transform([v])[0]) for v in y_test]
    print("\nTrain class distribution:")
    print(pd.Series(train_labels).value_counts().sort_index().to_string())
    print("\nTest class distribution:")
    print(pd.Series(test_labels).value_counts().sort_index().to_string())

    evaluate_baseline_configs(
        x_train=x_train,
        x_test=x_test,
        y_train=y_train,
        y_test=y_test,
        random_state=args.random_state,
    )

    model_families = ["LogisticRegression", "MultinomialNB", "LinearSVC", "RandomForest"]
    tuned_results: list[dict[str, Any]] = []
    for model_name in model_families:
        print(f"\n=== Tuning {model_name} ===")
        tuned = tune_model_family(
            model_name=model_name,
            x_train=x_train,
            x_test=x_test,
            y_train=y_train,
            y_test=y_test,
            random_state=args.random_state,
        )
        tuned_results.append(tuned)
        print(f"Best params: {tuned['best_params']}")
        print(f"Best CV weighted F1: {tuned['best_cv_f1']:.4f}")

    tuned_df = print_tuning_summary(tuned_results)
    best_model_name = str(tuned_df.iloc[0]["model_name"])
    best_result = next(item for item in tuned_results if item["model_name"] == best_model_name)

    print("\n=== Best Tuned Model ===")
    print(f"Model: {best_result['model_name']}")
    print(f"Params: {best_result['best_params']}")
    print(f"Supports predict_proba: {bool(best_result['supports_predict_proba'])}")
    print(f"Supports decision_function: {bool(best_result['supports_decision_function'])}")

    if best_result["model_name"] == "LinearSVC":
        print(
            "Note: LinearSVC does not provide calibrated probabilities by default; "
            "confidence may require scaling or fallback logic."
        )

    print("\n=== Classification Report (Best Model) ===")
    print(
        classification_report(
            y_test,
            best_result["test_pred"],
            target_names=[str(c) for c in label_encoder.classes_],
            zero_division=0,
        )
    )

    print_per_class_f1(y_true=y_test, y_pred=best_result["test_pred"], label_encoder=label_encoder)

    matrix_df = print_confusion_matrix_table(
        y_true=y_test,
        y_pred=best_result["test_pred"],
        label_encoder=label_encoder,
    )
    print_most_confused_pairs(matrix_df=matrix_df, top_n=10)

    misclassified_df = build_misclassified_examples(
        x_test=x_test,
        y_true=y_test,
        y_pred=best_result["test_pred"],
        label_encoder=label_encoder,
    )

    print("\n=== Top 20 Misclassified Examples ===")
    if misclassified_df.empty:
        print("No misclassified examples in test split.")
    else:
        print(misclassified_df.head(20).to_string(index=False))

    print_targeted_mistakes(misclassified_df)

    if args.show_top_features:
        print_top_linear_features_per_class(
            pipeline=best_result["pipeline"],
            label_encoder=label_encoder,
            top_n=15,
        )

    model_dir = Path(args.model_dir)
    if not model_dir.is_absolute():
        model_dir = (BASE_DIR / model_dir).resolve()

    report_dir = Path(args.report_dir) if args.report_dir.strip() else model_dir
    if not report_dir.is_absolute():
        report_dir = (BASE_DIR / report_dir).resolve()

    model_path, vectorizer_path, label_encoder_path = save_artifacts(
        model_dir=model_dir,
        pipeline=best_result["pipeline"],
        label_encoder=label_encoder,
    )

    print("\nSaved artifacts (best model):")
    print(f"- {model_path}")
    print(f"- {vectorizer_path}")
    print(f"- {label_encoder_path}")

    save_comparison_and_metrics(
        reporting_dir=report_dir,
        tuned_results=tuned_results,
        best_result=best_result,
        test_size=args.test_size,
        random_state=args.random_state,
    )
    print(f"\nSaved model comparison: {report_dir / 'model_comparison.csv'}")
    print(f"Saved metrics bundle: {report_dir / 'metrics.json'}")

    write_model_info_file(
        model_dir=model_dir,
        best_result=best_result,
        label_encoder=label_encoder,
        loaded_file_names=[p.name for p in dataset_paths],
        cleaned_rows=len(cleaned),
    )
    print(f"Saved model_info.json: {model_dir / 'model_info.json'}")

    summary_path = model_dir / "training_summary.json"
    save_training_summary(
        output_path=summary_path,
        loaded_files=[p.name for p in dataset_paths],
        cleaned_rows=len(cleaned),
        best_result=best_result,
    )
    print(f"Saved training summary: {summary_path}")

    if args.semi_supervised:
        semi = run_semi_supervised_self_training(
            x_train=x_train,
            y_train=y_train,
            x_test=x_test,
            y_test=y_test,
            label_encoder=label_encoder,
            best_pipeline_template=best_result["pipeline"],
            random_state=args.random_state,
            confidence_threshold=args.pseudo_confidence,
        )
        semi_path = report_dir / "semi_supervised_metrics.json"
        semi_path.write_text(json.dumps(_json_safe(semi), indent=2), encoding="utf-8")
        print(f"\nSemi-supervised benchmark written to: {semi_path}")
        print(json.dumps(semi, indent=2, default=str))


def main() -> None:
    args = parse_args()
    train_pipeline(args)


if __name__ == "__main__":
    main()
