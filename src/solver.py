# src/solver.py

from typing import Dict, List

import pandas as pd
import pulp


def solve_model(model: pulp.LpProblem) -> str:
    """
    Solve the given PuLP model using CBC solver.
    Returns the solver status string.
    """
    solver = pulp.PULP_CBC_CMD(msg=False)
    model.solve(solver)
    status = pulp.LpStatus[model.status]
    print(f"[solver] Solver status: {status}")
    return status


def extract_solution(
    df: pd.DataFrame,
    items: List[str],
    s: Dict[str, pulp.LpVariable],
    threshold: float = 1e-4,
) -> pd.DataFrame:
    """
    Extract the optimal quantities for items with servings > threshold.
    Converts servings → grams using Estimated_Serving_Weight_g per item.
    """
    rows = []
    weight_map = df.set_index("Food_Item")["Estimated_Serving_Weight_g"].to_dict()

    for item in items:
        servings = s[item].value()
        if servings is not None and servings > threshold:
            w = weight_map.get(item, 100.0)  # fallback if missing
            grams = servings * w
            rows.append([item, servings, grams])

    solution_df = pd.DataFrame(rows, columns=["Food_Item", "Servings", "Quantity (grams)"])
    print(f"[solver] Non-zero items in solution: {len(solution_df)}")
    return solution_df
