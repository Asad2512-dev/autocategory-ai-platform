import argparse
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = BASE_DIR / "data" / "training_dataset.csv"
DEFAULT_OUTPUT_PATH = BASE_DIR / "data" / "training_dataset.cleaned.csv"

CATEGORY_MAP = {
    "home and kitchen": "Home & Kitchen",
    "home & kitchen": "Home & Kitchen",
    "home": "Home",
    "electronics": "Electronics",
    "fashion": "Fashion",
    "books": "Books",
    "beauty": "Beauty",
    "sports": "Sports",
    "toys": "Toys",
}


def normalize_text(value: str) -> str:
    return " ".join(str(value).strip().split())


def normalize_category(value: str) -> str:
    raw = normalize_text(value)
    normalized = CATEGORY_MAP.get(raw.lower(), raw)
    return normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean training dataset CSV")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Input CSV path. Defaults to data/training_dataset.csv",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Output CSV path. Defaults to data/training_dataset.cleaned.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_path}")

    df = pd.read_csv(input_path)
    required_columns = {"title", "description", "category"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    cleaned = df[["title", "description", "category"]].copy()
    cleaned = cleaned.dropna(subset=["title", "description", "category"])

    cleaned.loc[:, "title"] = cleaned["title"].map(normalize_text)
    cleaned.loc[:, "description"] = cleaned["description"].map(normalize_text)
    cleaned.loc[:, "category"] = cleaned["category"].map(normalize_category)

    cleaned = cleaned[
        (cleaned["title"] != "")
        & (cleaned["description"] != "")
        & (cleaned["category"] != "")
    ]

    cleaned = cleaned.drop_duplicates(subset=["title", "description", "category"]) 
    cleaned = cleaned.sort_values(by=["category", "title"]).reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(output_path, index=False)

    print(f"Input rows: {len(df)}")
    print(f"Cleaned rows: {len(cleaned)}")
    print(f"Saved cleaned dataset to: {output_path}")


if __name__ == "__main__":
    main()
