"""Stage 06: kịch bản khuyến mãi có điều kiện. P10/P90 của kịch bản dùng độ rộng theo từng dòng của Stage 05
(Mondrian); xuất thêm bảng tổng hợp promotion_scenario_summary.csv.
"""
from src.common import *
import pandas as pd, numpy as np, joblib, json

o = od("06_promotion_scenarios")
d = pd.read_parquet(OUT / "03_feature_engineering" / "features.parquet")
features = [x for x in pd.read_csv(OUT / "03_feature_engineering" / "feature_list.csv").feature if x not in ("lag_7", "lag_14")]
winner = json.loads((OUT / "04_model_comparison" / "model_selection.json").read_text(encoding="utf-8"))["winner"]
dates = sorted(d.date.unique()); te = d[d.date >= dates[-HORIZON]].copy()
pr = pd.read_parquet(OUT / "05_probabilistic_forecast" / "probabilistic_predictions.parquet")
te = te.merge(pr[["date", "store_nbr", "family", "p10", "p50", "p90"]].rename(columns={"p10": "b10", "p50": "b50", "p90": "b90"}), on=["date", "store_nbr", "family"], how="left")
model = None if winner == "Seasonal Naive" else joblib.load(OUT / "04_model_comparison" / "models" / "selected_point_model.joblib")
rows = []
for label, val in {"No promotion": 0, "Current": None, "Low": 1, "Medium": 5, "High": 10}.items():
    x = te.copy()
    if val is not None: x["onpromotion"] = val
    if model is None:
        h = (x.date - x.date.min()).dt.days + 1; point = np.where(h <= 7, x.lag_7, np.where(h <= 14, x.lag_14, x.lag_21))
    else:
        point = np.clip(model.predict(x[features]), 0, None)
    x["p50"] = point; x["p10"] = np.clip(point - (x.b50 - x.b10), 0, None); x["p90"] = point + (x.b90 - x.b50)
    a = x.groupby(["store_nbr", "family"], as_index=False).agg(p10=("p10", "sum"), p50=("p50", "sum"), p90=("p90", "sum"))
    a["scenario"] = label; a["selected_model"] = winner; rows.append(a)
z = pd.concat(rows, ignore_index=True)
z = z.merge(z[z.scenario == "Current"][["store_nbr", "family", "p50"]].rename(columns={"p50": "current_p50"}), on=["store_nbr", "family"])
z["conditional_change_vs_current"] = z.p50 - z.current_p50
z.to_csv(o / "promotion_scenarios.csv", index=False)
z.groupby("scenario").agg(n=("p50", "size"), p10_mean=("p10", "mean"), p50_mean=("p50", "mean"), p90_mean=("p90", "mean"),
                          change_mean=("conditional_change_vs_current", "mean"), p50_total=("p50", "sum")).reset_index().to_csv(o / "promotion_scenario_summary.csv", index=False)
(o / "README.txt").write_text(f"Selected model: {winner}. Scenario differences are conditional predictions, NOT causal promotion effects.", encoding="utf-8")
print("Promotion scenarios use selected model:", winner)
