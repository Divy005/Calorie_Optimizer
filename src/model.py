# src/model.py

from dataclasses import dataclass
from typing import Dict, List, Tuple
import pandas as pd
import pulp
import re


# ------------------------------------------------------
# Helper: sanitize + add unique ID to guarantee no collisions
# ------------------------------------------------------
def safe_name(name: str, idx: int) -> str:
    """
    Replace characters unsafe for PuLP AND append the row index
    to ensure constraint names are always unique.
    """
    base = re.sub(r'[^A-Za-z0-9_]+', '_', name)
    return f"{base}_{idx}"


# ------------------------------------------------------
# User target + model config
# ------------------------------------------------------
@dataclass
class NutritionTargets:
    cal_target: float
    protein_target: float
    carb_target: float
    fat_target: float

    # servings are abstract; each serving has its own gram weight
    min_servings_per_item: float = 0.5
    max_servings_per_item: float = 3.0

    # global variety
    max_total_dishes: int = 15


# ------------------------------------------------------
# BUILD DIET MODEL
# ------------------------------------------------------
def build_diet_model(
    df: pd.DataFrame,
    targets: NutritionTargets,
) -> Tuple[pulp.LpProblem, Dict[str, pulp.LpVariable], Dict[str, pulp.LpVariable], List[str]]:

    # List of food items
    items = df["Food_Item"].tolist()

    meal_types = ["Breakfast", "Lunch", "Dinner", "Snack"]

    # Group items by meal
    meal_to_items = {
        meal: df[df["Meal_Type"] == meal]["Food_Item"].tolist()
        for meal in meal_types
    }

    # Initialize model
    model = pulp.LpProblem("Daily_Meal_Optimization", pulp.LpMinimize)

    # Variables
    s = pulp.LpVariable.dicts("servings", items, lowBound=0, cat="Continuous")
    y = pulp.LpVariable.dicts("select", items, lowBound=0, upBound=1, cat="Binary")

    # Slack variables for calories deviation
    s_plus = pulp.LpVariable("calorie_plus", lowBound=0)
    s_minus = pulp.LpVariable("calorie_minus", lowBound=0)

    # Objective function
    # Minimize |calorie deviation| + tiny penalty on total servings
    model += (
        s_plus + s_minus +
        0.001 * pulp.lpSum(s[item] for item in items)
    ), "Objective"

    # ------------------------------------------------------
    # Min/Max servings per item (with SAFE UNIQUE constraint names)
    # ------------------------------------------------------
    for idx, item in enumerate(items):
        cname = safe_name(item, idx)

        # max servings per item (if selected)
        model += (
            s[item] <= targets.max_servings_per_item * y[item],
            f"MaxServings_{cname}"
        )

        # min servings per item (if selected)
        model += (
            s[item] >= targets.min_servings_per_item * y[item],
            f"MinServings_{cname}"
        )

    # ------------------------------------------------------
    # Limit total number of dishes across the full day
    # ------------------------------------------------------
    model += (
        pulp.lpSum(y[i] for i in items) <= targets.max_total_dishes,
        "Max_Total_Dishes"
    )

    # ------------------------------------------------------
    # Meal-wise variety constraints:
    # Breakfast, Lunch, Dinner: 2–3 items
    # Snack: exactly 1 item
    # ------------------------------------------------------
    for meal in ["Breakfast", "Lunch", "Dinner"]:
        meal_items = meal_to_items.get(meal, [])
        if len(meal_items) >= 2:
            # at least 2 items
            model += (
                pulp.lpSum(y[i] for i in meal_items) >= 2,
                f"MinItems_{meal}"
            )
            # at most 3 items
            model += (
                pulp.lpSum(y[i] for i in meal_items) <= 3,
                f"MaxItems_{meal}"
            )

    # Snack: exactly 1 item (if there are snack items)
    snack_items = meal_to_items.get("Snack", [])
    if len(snack_items) >= 1:
        model += (
            pulp.lpSum(y[i] for i in snack_items) == 1,
            "ExactItems_Snack"
        )

    # ------------------------------------------------------
    # Access nutrient value by row index
    # Nutrients are per *serving* as given in dataset.
    # ------------------------------------------------------
    def v(idx: int, col: str) -> float:
        return float(df.loc[idx, col])

    # ------------------------------------------------------
    # Global nutrition constraints
    # Total = sum( nutrient_per_serving * servings )
    # ------------------------------------------------------

    # Calories
    model += (
        pulp.lpSum(
            v(i, "Calories (kcal)") * s[df.loc[i, "Food_Item"]]
            for i in df.index
        )
        == targets.cal_target + s_plus - s_minus
    ), "Calorie_Balance"

    # Protein >=
    model += (
        pulp.lpSum(
            v(i, "Protein (g)") * s[df.loc[i, "Food_Item"]]
            for i in df.index
        ) >= targets.protein_target
    ), "Protein_Min"

    # Fat <=
    model += (
        pulp.lpSum(
            v(i, "Fat (g)") * s[df.loc[i, "Food_Item"]]
            for i in df.index
        ) <= targets.fat_target
    ), "Fat_Max"

    # Carbs <=
    model += (
        pulp.lpSum(
            v(i, "Carbohydrates (g)") * s[df.loc[i, "Food_Item"]]
            for i in df.index
        ) <= targets.carb_target
    ), "Carb_Max"

    print("[model] Model built successfully with SAFE + UNIQUE constraint names and meal-wise item limits.")
    return model, s, y, items
