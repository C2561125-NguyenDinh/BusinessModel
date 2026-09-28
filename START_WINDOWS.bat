@echo off
setlocal
cd /d "%~dp0"
title Favorita 5-Model Final Pipeline
echo ============================================================
echo FAVORITA FINAL PIPELINE - 5 MODELS - ONE CLICK
echo ============================================================
where py >nul 2>nul
if errorlevel 1 (echo [ERROR] Python launcher not found.& pause& exit /b 1)
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv ".venv"
  if errorlevel 1 py -3.11 -m venv ".venv"
  if errorlevel 1 (echo [ERROR] Need Python 3.11 or 3.12.& pause& exit /b 1)
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :fail
if not exist "data\raw\train.csv" (echo [ERROR] Put Favorita train.csv in data\raw\ & pause& exit /b 1)

for %%F in (
  01_data_validation.py
  02_eda_decomposition.py
  03_feature_engineering.py
  04_train_compare_5_models.py
  05_probabilistic_forecasting.py
  06_promotion_scenarios.py
  07_inventory_decision.py
  08_genai_decision_support.py
  09_build_research_summary.py
  10_pipeline_smoke_test.py
  11_forecast_diagnostics.py
  12_case_studies.py
  13_build_report_ready.py
  14_sensitivity_experiments.py
) do (
  echo.
  echo ============================================================
  echo RUNNING %%F
  echo ============================================================
  ".venv\Scripts\python.exe" "%%F"
  if errorlevel 1 goto :fail
)
echo.
echo ALL PIPELINE STAGES PASSED. Opening dashboard...
".venv\Scripts\python.exe" -m streamlit run app.py
exit /b 0
:fail
echo.
echo [FAILED] Pipeline stopped. Read the error above.
pause
exit /b 1
