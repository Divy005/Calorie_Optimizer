# src/data_cleaning.py

from pathlib import Path
from typing import Optional

import pandas as pd

from .utils import ensure_dir, project_root

DATA_DIR = project_root() / "data"
RAW_DATA_PATH = DATA_DIR / "original_csv.csv"
CLEAN_DATA_PATH = DATA_DIR / "daily_food_nutrition_dataset_cleaned.csv"

REQUIRED_COLUMNS = [
    "Food_Item",
    "Category",
    "Calories (kcal)",
    "Protein (g)",
    "Carbohydrates (g)",
    "Fat (g)",
    "Meal_Type",
    "Estimated_Serving_Weight_g",
]


def clean_data(
    raw_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Load the raw dataset, perform basic cleaning, and save a cleaned version.

    Assumptions:
    - Nutrient values (calories, protein, etc.) are given per serving,
      where each serving has weight 'Estimated_Serving_Weight_g'.
    """
    ensure_dir(DATA_DIR)

    raw_path = raw_path or RAW_DATA_PATH
    output_path = output_path or CLEAN_DATA_PATH

    if not raw_path.exists():
        raise FileNotFoundError(
            f"Raw data file not found at {raw_path}. "
            f"Please place your dataset there as 'original_csv.csv'."
        )

    # Some lines might be malformed; skip them
    df = pd.read_csv(raw_path, on_bad_lines="skip")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")

    # Convert nutrient columns + serving weight to numeric
    numeric_cols = [
        c
        for c in df.columns
        if c
        not in [
            "Food_Item",
            "Category",
            "Meal_Type",
        ]
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows with missing critical values
    df = df.dropna(
        subset=[
            "Food_Item",
            "Calories (kcal)",
            "Protein (g)",
            "Carbohydrates (g)",
            "Fat (g)",
            "Meal_Type",
            "Estimated_Serving_Weight_g",
        ]
    )

    # Normalize strings
    df["Food_Item"] = df["Food_Item"].astype(str).str.strip()
    df["Category"] = df["Category"].astype(str).str.strip().str.title()
    df["Meal_Type"] = df["Meal_Type"].astype(str).str.strip().str.title()

    # Remove duplicates (Food_Item + Meal_Type)
    df = df.drop_duplicates(subset=["Food_Item", "Meal_Type"]).reset_index(drop=True)

    df.to_csv(output_path, index=False)
    print(f"[data_cleaning] Cleaned dataset saved to {output_path}")

    return df
