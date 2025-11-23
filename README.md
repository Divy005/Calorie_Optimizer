# 📊 Calorie Optimization Pipeline
### Automated Nutritional Optimization, Meal Planning, and Visualization

<p align="left">
<a href="#"><img src="https://img.shields.io/badge/Python-3.9+-blue.svg"></a>
<a href="#"><img src="https://img.shields.io/badge/Streamlit-1.0+-red.svg"></a>
<a href="#"><img src="https://img.shields.io/badge/PuLP-Linear%20Programming-green.svg"></a>
<a href="#"><img src="https://img.shields.io/badge/Data%20Science-Pandas%20%7C%20Matplotlib-yellow.svg"></a>
<a href="#"><img src="https://img.shields.io/badge/License-MIT-blue.svg"></a>
</p>

This repository implements a complete workflow for transforming a custom food nutrition dataset into a caloric-intake optimized daily meal plan using linear programming model. The pipeline performs data cleaning, visualization, optimization model construction, solver execution, analysis, and also provides an interactive Streamlit application.

---

## 🚀 Features  
### ✔ Full Data Pipeline  
- Raw → Cleaned → Model-Ready Dataset Processing  
- Automated validation & type normalization  

### ✔ Linear Programming Diet Optimization  
- PuLP-based LP/MIP solver  
- Per-meal constraints (Breakfast/Lunch/Dinner/Snacks)  
- Global nutritional constraints  
- Slack-based calorie balancing  

### ✔ Visualization Suite  
- Macro histograms  
- Calories vs Protein scatter  
- Optimal plan bar charts  

### ✔ Streamlit Front-End  
- Upload custom datasets  
- Dynamic configuration of targets  
- Real-time visualization & model execution  
- Export results (CSV + TXT)

---


## 📁 Project Structure
```
main.py
dataset_eda.ipynb
streamlit_app.py
requirements.txt
src/
    data_cleaning.py
    data_loader.py
    data_visualization.py
    model.py
    solver.py
    analysis.py
    utils.py
    __init__.py
data/
    original_csv.csv
    daily_food_nutrition_dataset_cleaned.csv
results/
```

---

## ⚙️ Pipeline Components

### ✔ Data Cleaning
`src/data_cleaning.py` loads and sanitizes the raw dataset. It:
- Validates required columns
- Converts nutrient fields to numeric types
- Removes duplicates
- Normalizes naming
- Saves output to `daily_food_nutrition_dataset_cleaned.csv`

### ✔ Data Loading
`src/data_loader.py` loads the cleaned dataset and triggers cleaning automatically if needed.

### ✔ Visualization
`src/data_visualization.py` generates:
- Macro-nutrient histograms
- Calories vs protein scatter plots
- A bar chart for the optimized day plan

Plots are written to ```results/plots/``` .

### ✔ Optimization Model
`src/model.py` defines a PuLP-based LP/MIP formulation with:
- Continuous servings variables and binary selection variables
- Per-meal constraints (Breakfast, Lunch, Dinner: 2–3 items; Snack: exactly 1)
- Item-level min/max serving limits
- Global nutritional constraints (calories, protein, fats, carbs)
- Calorie deviation slack variables
- Safe, unique constraint naming

### ✔ Solver
`src/solver.py` uses the CBC solver to find an optimal solution and extracts item-level results in servings and grams.

### ✔ Analysis
`src/analysis.py` computes:
- Total nutrient values for the optimized plan
- Deviations from user targets
- A meal-wise breakdown table including nutrient contributions

### ✔ Pipeline Orchestration
`main.py` coordinates all steps:
- Collects user nutritional targets
- Cleans and loads data
- Generates visualizations
- Builds and solves the optimization model
- Produces results CSVs, evaluation metrics, and plots

All outputs are saved under:
```
results/
results/plots/
```

---

## 💻 Streamlit Application
The repository includes an interactive UI in `streamlit_app.py`.  
It allows users to:
- Upload a custom CSV dataset
- Force-run cleaning or use project data
- Adjust nutritional targets and model parameters
- View real-time nutrient visualizations
- Inspect the selected optimal items
- View the meal-wise plan and evaluation metrics
- Download the generated results (CSV and TXT)

### ✔ Run the Streamlit App
```
streamlit run streamlit_app.py
```

---

## 🔗 Usage

### ✔ Install Dependencies
Create and activate the virtual environment:
```
python -m venv myenv
```
Activate the virtual environment:
- Windows:
  ```
  myenv\Scripts\activate
  ```
- Linux / MacOS:
  ```
  source myenv/bin/activate
  ```
Install all dependencies:
```
pip install -r requirements.txt
```

### ✔ Run the Pipeline (CLI)
Place your raw dataset at:
```
data/original_csv.csv
```

Run:
```
python main.py
```

### ✔ Run the Streamlit App
```
streamlit run streamlit_app.py
```

---

## 🌟 Output Files
The pipeline generates:
- `optimal_solution.csv` — items selected and their quantities
- `solution_explanation.csv` — meal-wise formatted output
- `metrics.txt` — nutrient totals and deviations
- Visualization PNGs in `results/plots/`
