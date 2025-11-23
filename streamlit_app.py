# streamlit_app.py
"""
Streamlit app for the Daily Meal Planner optimization pipeline.
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Import project modules
from src.data_cleaning import clean_data, CLEAN_DATA_PATH, RAW_DATA_PATH
from src.data_loader import load_data
from src.data_visualization import (
    plot_macro_histograms,
    plot_calories_vs_protein,
    plot_optimal_solution,
)
from src.model import NutritionTargets, build_diet_model
from src.solver import solve_model, extract_solution
from src.analysis import build_meal_plan_table, evaluate_solution
from src.utils import ensure_dir

RESULTS_DIR = PROJECT_ROOT / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
ensure_dir(RESULTS_DIR)
ensure_dir(PLOTS_DIR)

# ---------------------------------------------
# Streamlit UI
# ---------------------------------------------
st.set_page_config(page_title="Daily Meal Planner (Optimizer)", layout="wide")

st.sidebar.title("Daily Meal Planner — Settings")

st.sidebar.markdown("### Nutritional Targets")
cal_target = st.sidebar.number_input("Total Calories (kcal)", value=2000.0)
protein_target = st.sidebar.number_input("Protein (g) [min]", value=75.0)
carb_target = st.sidebar.number_input("Carbohydrates (g) [max]", value=250.0)
fat_target = st.sidebar.number_input("Fat (g) [max]", value=60.0)

st.sidebar.markdown("---")
st.sidebar.markdown("### Model Parameters")
min_serv = st.sidebar.number_input("Min servings per item", value=0.5)
max_serv = st.sidebar.number_input("Max servings per item", value=3.0)
max_total_dishes = st.sidebar.number_input("Max distinct dishes", value=15)

st.sidebar.markdown("---")
uploaded = st.sidebar.file_uploader("Upload custom dataset (.csv)", type=["csv"])
force_clean = st.sidebar.checkbox("Force data cleaning")

run = st.sidebar.button("Run Optimization")

# ---------------------------------------------
# Dataset Loading
# ---------------------------------------------
st.title("Daily Meal Planner — Optimization Engine")

if uploaded:
    st.success("Custom CSV uploaded.")
    df_uploaded = pd.read_csv(uploaded, on_bad_lines="skip")
    temp_raw = PROJECT_ROOT / "data" / "uploaded_raw.csv"
    ensure_dir(temp_raw.parent)
    df_uploaded.to_csv(temp_raw, index=False)
    df_clean = clean_data(raw_path=temp_raw, output_path=PROJECT_ROOT / "data" / "uploaded_cleaned.csv")
    df = df_clean
else:
    if force_clean or not CLEAN_DATA_PATH.exists():
        st.info("Cleaning project dataset...")
        df = clean_data()
    else:
        df = load_data()

st.markdown("### Preview of Dataset")
st.dataframe(df.head(15))

# ---------------------------------------------
# RUN PIPELINE
# ---------------------------------------------
if run:
    with st.spinner("Running optimization..."):
        # -------------------------------------
        # Pre-Optimization Plots (using your functions)
        # -------------------------------------
        st.markdown("## Pre-Optimization Visualizations")
        plot_macro_histograms(df)               # saves to results/plots/
        plot_calories_vs_protein(df)            # saves to results/plots/

        st.success("Plots saved to /results/plots/. You can view them directly in the folder.")

        st.markdown("### Preview of Saved Plots")

        # Display saved macro histogram
        macro_path = PLOTS_DIR / "macro_histograms.png"
        if macro_path.exists():
            st.image(str(macro_path), caption="Macro Histograms")

        # Display saved calories vs protein scatter
        scatter_path = PLOTS_DIR / "calories_vs_protein.png"
        if scatter_path.exists():
            st.image(str(scatter_path), caption="Calories vs Protein")


        # -------------------------------------
        # Build & Solve Model
        # -------------------------------------
        st.markdown("## Optimization Model")

        targets = NutritionTargets(
            cal_target=cal_target,
            protein_target=protein_target,
            carb_target=carb_target,
            fat_target=fat_target,
            min_servings_per_item=min_serv,
            max_servings_per_item=max_serv,
            max_total_dishes=max_total_dishes,
        )

        model, s_vars, y_vars, items = build_diet_model(df, targets)
        st.info("Model built successfully.")

        status = solve_model(model)
        st.write(f"Solver Status: **{status}**")

        if status != "Optimal":
            st.warning("The solution is not optimal. Consider relaxing constraints.")

        # -------------------------------------
        # Extract Solution
        # -------------------------------------
        solution_df = extract_solution(df, items, s_vars)
        solution_path = RESULTS_DIR / "optimal_solution.csv"
        solution_df.to_csv(solution_path, index=False)

        st.markdown("## Optimal Solution")
        st.dataframe(solution_df)

        # -------------------------------------
        # Meal Plan
        # -------------------------------------
        plan_df = build_meal_plan_table(df, solution_df)
        plan_path = RESULTS_DIR / "solution_explanation.csv"
        plan_df.to_csv(plan_path, index=False)

        st.markdown("## Meal-wise Plan")
        st.dataframe(plan_df)

        # -------------------------------------
        # Metrics
        # -------------------------------------
        st.markdown("## Evaluation Metrics")
        metrics = evaluate_solution(df, solution_df, cal_target, protein_target, fat_target, carb_target)

        metrics_path = RESULTS_DIR / "metrics.txt"
        with open(metrics_path, "w") as f:
            for k, v in metrics.items():
                f.write(f"{k}: {v}\n")

        st.table(pd.DataFrame.from_dict(metrics, orient="index", columns=["Value"]))

        # -------------------------------------
        # Post-Optimization Plot
        # -------------------------------------
        plot_optimal_solution(solution_df)   # uses your existing function

        st.success("All plots & results saved to /results/.")

        # Display saved optimal solution bar plot
        optimal_plot_path = PLOTS_DIR / "optimal_solution_bar.png"
        if optimal_plot_path.exists():
            st.image(str(optimal_plot_path), caption="Optimal Solution (grams)")


        st.info("Check results/ and results/plots/ folders.")

# ---------------------------------------------
# Footer
# ---------------------------------------------
st.markdown("---")
st.caption("Powered by PuLP + Streamlit + your custom optimization pipeline.")
