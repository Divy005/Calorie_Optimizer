# src/analysis.py

from typing import Any, Dict

import pandas as pd


def compute_totals(df: pd.DataFrame, solution_df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute total nutrients for the optimal solution.

    Nutrient columns in df are per serving.
    We multiply per-serving values by the number of servings.
    """
    merged = solution_df.merge(df, on="Food_Item", how="left")

    def total(col: str) -> float:
        if col not in merged.columns:
            return 0.0
        return float((merged[col] * merged["Servings"]).sum())

    totals = {
        "Total Calories (kcal)": total("Calories (kcal)"),
        "Total Protein (g)": total("Protein (g)"),
        "Total Fat (g)": total("Fat (g)"),
        "Total Carbohydrates (g)": total("Carbohydrates (g)"),
        "Total Sugars (g)": total("Sugars (g)"),
        "Total Fiber (g)": total("Fiber (g)"),
        "Total Sodium (mg)": total("Sodium (mg)"),
    }

    return totals


def evaluate_solution(
    df: pd.DataFrame,
    solution_df: pd.DataFrame,
    cal_target: float,
    protein_target: float,
    fat_target: float,
    carb_target: float,
) -> Dict[str, Any]:
    """
    Compare solution totals vs user targets.
    """
    totals = compute_totals(df, solution_df)
    metrics: Dict[str, Any] = {}
    metrics.update(totals)

    metrics["Calorie Deviation (kcal)"] = totals["Total Calories (kcal)"] - cal_target
    metrics["Protein Slack (g)"] = totals["Total Protein (g)"] - protein_target
    metrics["Fat Slack (g)"] = fat_target - totals["Total Fat (g)"]
    metrics["Carb Slack (g)"] = carb_target - totals["Total Carbohydrates (g)"]

    print("[analysis] Evaluation metrics computed.")
    return metrics


def build_meal_plan_table(df: pd.DataFrame, solution_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a detailed table grouped by Meal_Type showing the final plan in grams.
    """
    merged = solution_df.merge(df, on="Food_Item", how="left")

    merged["Calories Contribution (kcal)"] = (
        merged["Calories (kcal)"] * merged["Servings"]
    )
    merged["Protein Contribution (g)"] = (
        merged["Protein (g)"] * merged["Servings"]
    )
    merged["Carb Contribution (g)"] = (
        merged["Carbohydrates (g)"] * merged["Servings"]
    )

    cols = [
        "Meal_Type",
        "Food_Item",
        "Servings",
        "Quantity (grams)",
        "Calories Contribution (kcal)",
        "Protein Contribution (g)",
        "Carb Contribution (g)",
    ]

    plan = merged[cols].sort_values(
        by=["Meal_Type", "Calories Contribution (kcal)"],
        ascending=[True, False],
    ).reset_index(drop=True)

    print("[analysis] Meal-wise plan table constructed.")
    return plan
