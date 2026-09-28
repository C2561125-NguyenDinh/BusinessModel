from src.common import *
import pandas as pd, numpy as np, json
need=["01_data_validation/data_quality.csv","02_eda_decomposition/stl_weekly.csv","03_feature_engineering/features.parquet",
"04_model_comparison/final_holdout_metrics.csv","04_model_comparison/model_selection.json","05_probabilistic_forecast/probabilistic_predictions.parquet",
"06_promotion_scenarios/promotion_scenarios.csv","07_inventory_decision/inventory_recommendations.csv",
"08_genai_decision_support/decision_cases.jsonl","09_research_summary/research_summary.json"]
missing=[x for x in need if not (OUT/x).exists()]
if missing: raise FileNotFoundError("Missing outputs: "+str(missing))
sel=json.loads((OUT/"04_model_comparison"/"model_selection.json").read_text(encoding="utf-8"))
if sel.get("final_holdout_used_for_selection") is not False: raise AssertionError("Final holdout must not be used for model selection")
pr=pd.read_parquet(OUT/"05_probabilistic_forecast"/"probabilistic_predictions.parquet")
if not ((pr.p10<=pr.p50)&(pr.p50<=pr.p90)).all(): raise AssertionError("Quantile crossing detected")
if pr[["p10","p50","p90"]].isna().any().any(): raise AssertionError("Missing probabilistic predictions")
fm=pd.read_csv(OUT/"04_model_comparison"/"final_holdout_metrics.csv")
if len(fm)!=5 or not np.isfinite(fm[["MAE","RMSE","WAPE"]].to_numpy()).all(): raise AssertionError("Invalid 5-model holdout metrics")
print("PIPELINE OUTPUT + METHODOLOGICAL SMOKE TEST: PASS")
