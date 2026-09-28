"""Stage 05: P10/P50/P90 bằng khoảng phần dư split-conformal theo nhóm quy mô (Mondrian).

Chia cửa sổ hiệu chỉnh (16 ngày trước tập kiểm tra cuối) thành 10 nhóm theo dự báo điểm (biết tại thời điểm
dự báo), lấy phân vị 0,1/0,5/0,9 của phần dư trong từng nhóm và áp cho dòng kiểm tra cùng nhóm.
Mô hình tính phần dư được huấn luyện trên dữ liệu trước cửa sổ hiệu chỉnh với CÙNG quy tắc dữ liệu của Stage 04.
"""
from src.common import *
import pandas as pd, numpy as np, joblib, json, importlib.util

o = od("05_probabilistic_forecast")
d = pd.read_parquet(OUT / "03_feature_engineering" / "features.parquet")
features = [x for x in pd.read_csv(OUT / "03_feature_engineering" / "feature_list.csv").feature if x not in ("lag_7", "lag_14")]
winner = json.loads((OUT / "04_model_comparison" / "model_selection.json").read_text(encoding="utf-8"))["winner"]
dates = np.array(sorted(d.date.unique())); hold = dates[-HORIZON:]; cd = dates[-2 * HORIZON:-HORIZON]
te = d[d.date.isin(hold)].copy(); cal = d[d.date.isin(cd)].copy(); fit_data = d[d.date < cd[0]]
spec = importlib.util.spec_from_file_location("s04", ROOT / "04_train_compare_5_models.py")


def seasonal_naive(va):
    h = (va.date - va.date.min()).dt.days + 1
    return np.where(h <= 7, va.lag_7, np.where(h <= 14, va.lag_14, va.lag_21))


if winner == "Seasonal Naive":
    cp, point = seasonal_naive(cal), seasonal_naive(te)
else:
    from sklearn.base import clone
    final = joblib.load(OUT / "04_model_comparison" / "models" / "selected_point_model.joblib")
    m = clone(final); tr = fit_data.sample(600000, random_state=SEED) if (winner == "Random Forest" and len(fit_data) > 600000) else fit_data
    m.fit(tr[features], tr.sales)
    cp = np.clip(m.predict(cal[features]), 0, None); point = np.clip(final.predict(te[features]), 0, None)
res = cal.sales.values - cp
edges = np.unique(np.quantile(cp, np.linspace(0, 1, 11)))
bc = np.clip(np.searchsorted(edges, cp, side="right") - 1, 0, len(edges) - 2)
bt = np.clip(np.searchsorted(edges, point, side="right") - 1, 0, len(edges) - 2)
Q = np.array([np.quantile(res[bc == b], [.1, .5, .9]) for b in range(len(edges) - 1)])
pd.DataFrame({"bin": range(len(edges) - 1), "lower_edge": edges[:-1], "upper_edge": edges[1:], "q10": Q[:, 0], "q50": Q[:, 1], "q90": Q[:, 2],
              "n_cal": [int((bc == b).sum()) for b in range(len(edges) - 1)]}).to_csv(o / "conformal_bins.csv", index=False)
P = np.sort(np.column_stack([np.clip(point + Q[bt, 0], 0, None), np.clip(point + Q[bt, 1], 0, None), np.clip(point + Q[bt, 2], 0, None)]), axis=1)
te["point"] = point; te["p10"], te["p50"], te["p90"] = P[:, 0], P[:, 1], P[:, 2]


def pin(y, q, a):
    e = np.asarray(y) - np.asarray(q); return float(np.mean(np.maximum(a * e, (a - 1) * e)))


method = f"Mondrian split-conformal residual intervals (10 bins of point forecast) around selected {winner}"
met = {"selected_model": winner, "uncertainty_method": method, "Pinball_P10": pin(te.sales, te.p10, .1), "Pinball_P50": pin(te.sales, te.p50, .5),
       "Pinball_P90": pin(te.sales, te.p90, .9), "Coverage_P10_P90": float(((te.sales >= te.p10) & (te.sales <= te.p90)).mean()),
       "Mean_interval_width": float((te.p90 - te.p10).mean())}
pd.DataFrame([met]).to_csv(o / "probabilistic_metrics.csv", index=False)
te[["date", "store_nbr", "family", "sales", "onpromotion", "point", "p10", "p50", "p90"]].to_parquet(o / "probabilistic_predictions.parquet", index=False)
save_json({"selected_model": winner, "method": method, "calibration_window": [str(pd.Timestamp(cd[0]).date()), str(pd.Timestamp(cd[-1]).date())]}, o / "probabilistic_method.json")
print(met)
