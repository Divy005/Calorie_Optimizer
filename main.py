# main.py
from src.analysis import build_meal_plan_table, evaluate_solution
from src.data_cleaning import clean_data
from src.data_loader import load_data
from src.data_visualization import (
    plot_calories_vs_protein,
    plot_macro_histograms,
    plot_optimal_solution,
)
from src.model import NutritionTargets, build_diet_model
from src.solver import extract_solution, solve_model
from src.utils import ensure_dir, project_root

def ask_float(prompt: str, default: float) -> float:
    raw = input(f"{prompt} [default = {default}]: ").strip()
    if raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        print("Invalid input, using default.")
        return default


def main() -> None:
    root = project_root()
    results_dir = root / "results"
    ensure_dir(results_dir)

    print("Daily Meal Planner (Breakfast + Lunch + Dinner + Snacks)")

    # Ask user for targets
    print("\nEnter your daily nutritional targets (press Enter to use defaults):")
    cal_target = ask_float("Total Calories (kcal)", 2000.0)
    protein_target = ask_float("Protein (g) [min]", 75.0)
    carb_target = ask_float("Carbohydrates (g) [max]", 250.0)
    fat_target = ask_float("Fat (g) [max]", 60.0)

    # Data cleaning
    print("\nStep 1: Cleaning data")
    clean_data()

    # Load cleaned data
    print("Step 2: Loading data")
    df = load_data()

    # Pre-optimization visualizations
    print("Step 3: Pre-optimization visualizations")
    plot_macro_histograms(df)
    plot_calories_vs_protein(df)

    # Build model
    print("Step 4: Building optimization model")
    targets = NutritionTargets(
        cal_target=cal_target,
        protein_target=protein_target,
        carb_target=carb_target,
        fat_target=fat_target,
        min_servings_per_item=0.5,
        max_servings_per_item=3.0,
        max_total_dishes=15,
    )
    model, s, y, items = build_diet_model(df, targets)

    # Solve model
    print("Step 5: Solving model")
    status = solve_model(model)
    if status != "Optimal":
        print("Warning: Solution status is not Optimal. You may want to relax constraints.")

    # Extract solution (servings → grams)
    print("Step 6: Extracting solution")
    solution_df = extract_solution(df, items, s)
    solution_path = results_dir / "optimal_solution.csv"
    solution_df.to_csv(solution_path, index=False)
    print(f"Optimal solution saved to {solution_path}")

    # Build meal-wise plan table
    print("Step 7: Building meal-wise plan table")
    plan_df = build_meal_plan_table(df, solution_df)
    plan_path = results_dir / "solution_explanation.csv"
    plan_df.to_csv(plan_path, index=False)
    print(f"Meal-wise plan saved to {plan_path}")

    # Evaluate totals vs targets
    print("Step 8: Evaluating totals vs targets")
    metrics = evaluate_solution(df, solution_df, cal_target, protein_target, fat_target, carb_target)
    metrics_path = results_dir / "metrics.txt"
    with open(metrics_path, "w") as f:
        for k, v in metrics.items():
            f.write(f"{k}: {v}\n")
    print(f"Metrics saved to {metrics_path}")

    print("\nSummary Metrics")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    # Post-optimization visualization
    print("Step 9: Plotting optimal solution")
    plot_optimal_solution(solution_df)

    print("\nPipeline completed successfully.")
    print("Check the 'results/' folder for CSVs, metrics, and plots.")


if __name__ == "__main__":
    main()
