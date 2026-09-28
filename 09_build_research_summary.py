from src.common import *
import pandas as pd, json
o = od("09_research_summary")
sel = json.loads((OUT / "04_model_comparison" / "model_selection.json").read_text(encoding="utf-8"))
cv = pd.read_csv(OUT / "04_model_comparison" / "model_comparison_summary.csv")
fh = pd.read_csv(OUT / "04_model_comparison" / "final_holdout_metrics.csv")
pm = pd.read_csv(OUT / "05_probabilistic_forecast" / "probabilistic_metrics.csv")
inv = pd.read_csv(OUT / "07_inventory_decision" / "inventory_recommendations.csv")
winner = sel["winner"]; wr = fh[fh.model == winner].iloc[0]
summary = {"pipeline_version": sel.get("pipeline_version", "1.0"), "selected_model": winner, "selection_rule": sel["selection_metric"],
           "selected_before_final_holdout": True, "selected_model_final_holdout_metrics": wr.to_dict(), "probabilistic_method": pm.uncertainty_method.iloc[0],
           "probabilistic_metrics": pm.iloc[0].to_dict(), "inventory_scenario_rows": len(inv), "risk_counts": inv.risk.value_counts().to_dict(),
           "scientific_limits": ["Promotion what-if is a conditional prediction, not a causal effect; onpromotion is not a discount %.",
                                 "Inventory outputs use explicit scenario assumptions (inventory position = 0.8 × P50, Cu = 3, Co = 1) because actual inventory/lead-time/cost are absent.",
                                 "Feature importance is predictive, not causal.",
                                 "Random Forest is trained on a 600,000-row sample for computational reasons; other models use all rows.",
                                 "Only three rolling-origin folds are used; differences smaller than the fold standard deviation should not be over-interpreted.",
                                 "Summing daily quantiles over 16 days is descriptive and is not the exact quantile of total demand.",
                                 "GenAI layer runs rule-based unless an API key is supplied; LLM text must pass a numeric grounding check."]}
save_json(summary, o / "research_summary.json"); cv.to_csv(o / "cv_summary_copy.csv", index=False); fh.to_csv(o / "final_metrics_copy.csv", index=False)
print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
