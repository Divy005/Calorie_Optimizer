# src/data_visualization.py

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd

from .utils import ensure_dir, project_root

RESULTS_DIR = project_root() / "results"
PLOTS_DIR = RESULTS_DIR / "plots"


def plot_macro_histograms(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Plot histograms for calories and macronutrients across all foods.
    """
    # Fixed the function name to the correct ensure_dir
    ensure_dir(PLOTS_DIR)
    output_path = output_path or (PLOTS_DIR / "macro_histograms.png")

    macro_cols = [
        "Calories (kcal)",
        "Protein (g)",
        "Fat (g)",
        "Carbohydrates (g)",
        "Sugars (g)",
        "Fiber (g)",
    ]
    existing = [c for c in macro_cols if c in df.columns]

    if not existing:
        print("[data_visualization] No macro columns found to plot.")
        return

    df[existing].hist(bins=20, figsize=(12, 8))
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"[data_visualization] Macro histograms saved to {output_path}")


def plot_calories_vs_protein(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Scatter plot of calories vs protein to show nutrient density per serving.
    """
    ensure_dir(PLOTS_DIR)
    output_path = output_path or (PLOTS_DIR / "calories_vs_protein.png")

   
    if "Calories_kcal" not in df.columns or "Protein_g" not in df.columns:
        print("[data_visualization] Required columns for scatter plot not found.")
        return

    plt.figure()
    plt.scatter(df["Calories (kcal)"], df["Protein (g)"])
    plt.xlabel("Calories (kcal) per serving")
    plt.ylabel("Protein (g) per serving")
    plt.title("Calories vs Protein per Serving")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"[data_visualization] Calories vs Protein plot saved to {output_path}")


def plot_optimal_solution(solution_df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Bar plot of quantity (grams) for each selected item in the optimal plan.
    """
    ensure_dir(PLOTS_DIR)
    output_path = output_path or (PLOTS_DIR / "optimal_solution_bar.png")

    if solution_df.empty:
        print("[data_visualization] Solution is empty; no plot generated.")
        return

    plt.figure(figsize=(12, 6))
    plt.bar(solution_df["Food_Item"], solution_df["Quantity (grams)"])
    plt.xticks(rotation=90)
    plt.ylabel("Quantity (grams)")
    plt.title("Optimal Day Plan - Items (in grams)")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"[data_visualization] Optimal solution bar plot saved to {output_path}")
