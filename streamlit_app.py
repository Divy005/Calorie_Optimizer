# streamlit_app.py
"""
Streamlit app for the Daily Meal Planner optimization pipeline.

Place this file at the project root (same level as `main.py` and `src/`).
Run with: `streamlit run streamlit_app.py`
"""

import sys
from pathlib import Path
import io

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Ensure project root is on sys.path so `src` can be imported reliably
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Import your modules
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

# Results paths (inside project)
RESULTS_DIR = PROJECT_ROOT / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
ensure_dir(RESULTS_DIR)
ensure_dir(PLOTS_DIR)

st.set_page_config(page_title="Daily Meal Planner (Optimizer)", layout="wide")

# ---- Sidebar: Inputs ----
st.sidebar.title("Daily Meal Planner — Settings")

st.sidebar.markdown("**Nutritional targets** (press Enter to accept defaults):")
cal_target = st.sidebar.number_input("Total Calories (kcal)", value=2000.0, step=50.0)
protein_target = st.sidebar.number_input("Protein (g) [min]", value=75.0, step=5.0)
carb_target = st.sidebar.number_input("Carbohydrates (g) [max]", value=250.0, step=5.0)
fat_target = st.sidebar.number_input("Fat (g) [max]", value=60.0, step=5.0)

st.sidebar.markdown("---")
st.sidebar.markdown("**Model parameters**")
min_serv = st.sidebar.number_input("Min servings per item", value=0.5, step=0.1)
max_serv = st.sidebar.number_input("Max servings per item", value=3.0, step=0.1)
max_total_dishes = st.sidebar.number_input("Max total distinct dishes", value=15, step=1)

st.sidebar.markdown("---")
st.sidebar.markdown("**Dataset options**")

# Allow user to upload dataset or use the project's raw/cleaned files
uploaded = st.sidebar.file_uploader(
    "Upload custom CSV (optional). If you don't upload, the project's data/original_csv.csv will be used.",
    type=["csv"],
)

use_raw_run_clean = st.sidebar.checkbox("Force run data cleaning step", value=False)

run_button = st.sidebar.button("Run optimization")

# ---- Main layout ----
st.title("Daily Meal Planner — Optimization")
st.markdown("Interactive front-end for your LP-based diet optimizer.")

# Show dataset info
st.markdown("## Dataset")
st.write(
    "You can upload a CSV (must contain required columns), or the app will use the project's `data/original_csv.csv`."
)

# Helper: load dataframe (cache to speed UI)
@st.cache_data(show_spinner=False)
def _load_df_from_upload(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        df = pd.read_csv(uploaded_file, on_bad_lines="skip")
    except Exception as e:
        st.error(f"Failed to read uploaded CSV: {e}")
        return None
    return df

uploaded_df = _load_df_from_upload(uploaded)

# If user provided uploaded file, preview it and offer to clean/save
if uploaded_df is not None:
    st.success("Uploaded CSV loaded (preview below).")
    st.dataframe(uploaded_df.head(10))
    st.markdown("If you'd like to use the uploaded dataset for optimization, it will be used as-is (cleaning will be attempted).")
else:
    st.info(f"No upload. Will use `{RAW_DATA_PATH.name}` from project `data/` (cleaning will run if necessary).")
    st.write(f"Project raw path: `{RAW_DATA_PATH}`")
    st.write(f"Project cleaned path: `{CLEAN_DATA_PATH}`")

# ---- Run optimization pipeline ----
if run_button:
    with st.spinner("Running pipeline..."):
        # 1) Choose source CSV path / perform cleaning
        try:
            if uploaded_df is not None:
                # Save uploaded to a temp file and run cleaning on it
                temp_raw = PROJECT_ROOT / "data" / "uploaded_raw.csv"
                ensure_dir(PROJECT_ROOT / "data")
                uploaded_df.to_csv(temp_raw, index=False)
                df_clean = clean_data(raw_path=temp_raw, output_path=PROJECT_ROOT / "data" / "uploaded_cleaned.csv")
                df = df_clean
                st.success("Uploaded dataset cleaned and loaded.")
            else:
                # Use project original file; clean if requested or if cleaned missing
                if use_raw_run_clean or not (PROJECT_ROOT / "data" / "daily_food_nutrition_dataset_cleaned.csv").exists():
                    st.info("Cleaning project raw data...")
                    df_clean = clean_data()  # uses default RAW_DATA_PATH -> outputs default CLEAN_DATA_PATH
                    df = df_clean
                else:
                    df = load_data()
        except Exception as e:
            st.exception(f"Data loading/cleaning failed: {e}")
            st.stop()

        st.markdown("### Data preview (first 15 rows)")
        st.dataframe(df.head(15))

        # 2) Pre-optimization visualizations
        st.markdown("### Pre-optimization Visualizations")
        # calories vs protein scatter
        fig1 = plt.figure()
        try:
            plt.scatter(df["Calories (kcal)"], df["Protein (g)"])
            plt.xlabel("Calories (kcal) per serving")
            plt.ylabel("Protein (g) per serving")
            plt.title("Calories vs Protein per Serving")
            plt.tight_layout()
            st.pyplot(fig1)
        finally:
            plt.close(fig1)

        # macro histograms
        fig2 = plt.figure(figsize=(10, 6))
        try:
            macro_cols = [c for c in ["Calories (kcal)", "Protein (g)", "Fat (g)", "Carbohydrates (g)", "Sugars (g)", "Fiber (g)"] if c in df.columns]
            if macro_cols:
                df[macro_cols].hist(bins=20, figsize=(12, 6))
                plt.tight_layout()
                st.pyplot(plt.gcf())
            else:
                st.info("No macro columns found for histograms.")
        finally:
            plt.close('all')

        # 3) Build and solve model
        st.markdown("### Building and Solving Optimization Model")
        targets = NutritionTargets(
            cal_target=float(cal_target),
            protein_target=float(protein_target),
            carb_target=float(carb_target),
            fat_target=float(fat_target),
            min_servings_per_item=float(min_serv),
            max_servings_per_item=float(max_serv),
            max_total_dishes=int(max_total_dishes),
        )

        try:
            model, s_vars, y_vars, items = build_diet_model(df, targets)
        except Exception as e:
            st.exception(f"Model building failed: {e}")
            st.stop()

        st.info("Model built. Solving...")
        status = solve_model(model)
        st.write(f"Solver status: **{status}**")
        if status != "Optimal":
            st.warning("Solver did not find an optimal solution. Consider relaxing targets or changing model parameters.")

        # 4) Extract solution
        solution_df = extract_solution(df, items, s_vars)
        if solution_df.empty:
            st.warning("No non-zero solution items found. Nothing to show.")
        else:
            st.markdown("### Optimal Solution (selected items)")
            st.dataframe(solution_df)

            # 5) Meal plan table
            plan_df = build_meal_plan_table(df, solution_df)
            st.markdown("### Meal-wise Plan")
            st.dataframe(plan_df)

            # 6) Metrics
            metrics = evaluate_solution(df, solution_df, targets.cal_target, targets.protein_target, targets.fat_target, targets.carb_target)
            st.markdown("### Metrics vs Targets")
            st.table(pd.DataFrame.from_dict(metrics, orient="index", columns=["Value"]))

            # 7) Post-optimization plot (bar)
            fig3 = plt.figure(figsize=(12, 6))
            try:
                plt.bar(solution_df["Food_Item"], solution_df["Quantity (grams)"])
                plt.xticks(rotation=90)
                plt.ylabel("Quantity (grams)")
                plt.title("Optimal Day Plan - Items (in grams)")
                plt.tight_layout()
                st.pyplot(fig3)
            finally:
                plt.close(fig3)

            # 8) Offer downloads: optimal_solution.csv, solution_explanation.csv, metrics.txt
            st.markdown("### Download results")
            csv_opt = solution_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download optimal_solution.csv", data=csv_opt, file_name="optimal_solution.csv", mime="text/csv")

            csv_plan = plan_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download solution_explanation.csv", data=csv_plan, file_name="solution_explanation.csv", mime="text/csv")

            metrics_txt = "\n".join(f"{k}: {v}" for k, v in metrics.items()).encode("utf-8")
            st.download_button("Download metrics.txt", data=metrics_txt, file_name="metrics.txt", mime="text/plain")

    st.success("Pipeline run complete.")

# ---- Footer / tips ----
st.markdown("---")
st.markdown(
    """
If you want tweaks:
- Add additional nutrient constraints (sodium, fiber) in `src/model.py`.
- Change objective (e.g., minimize cost) by modifying the objective in `src/model.py`.
- For a faster UI loop, try reducing dataset size or caching more intermediate steps.
"""
)
