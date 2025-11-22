# src/data_loader.py

from pathlib import Path
from typing import Optional

import pandas as pd

from .data_cleaning import CLEAN_DATA_PATH, clean_data


def load_data(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the cleaned dataset. If it does not exist, run the cleaning step first.
    """
    path = path or CLEAN_DATA_PATH

    if not path.exists():
        print("[data_loader] Cleaned data not found. Running data_cleaning...")
        clean_data()

    df = pd.read_csv(path)
    print(f"[data_loader] Loaded cleaned dataset from {path}. Rows = {len(df)}")
    return df
