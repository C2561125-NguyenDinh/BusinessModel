"""Stage 04: so sánh 5 mô hình bằng 3 lần kiểm định chéo cuốn chiếu + tập kiểm tra cuối 16 ngày.

Thiết kế:
  1) Seasonal Naive cố định gốc dự báo (origin-fixed): ngày h của cửa sổ dùng doanh số cùng thứ của tuần cuối
     trước gốc (lag_7 cho h = 1..7, lag_14 cho h = 8..14, lag_21 cho h = 15..16) → không dùng dữ liệu trong kỳ dự báo.
  2) Ridge chuẩn hóa đặc trưng (StandardScaler) trước khi phạt L2.
  3) LightGBM đặt subsample_freq = 1 để subsample = 0,85 có hiệu lực.
  4) XGBoost, LightGBM, Ridge huấn luyện trên toàn bộ dữ liệu; Random Forest dùng mẫu 600.000 dòng
     (ràng buộc tính toán, được ghi lại trong cột train_rows).
"""
from src.common import *
import pandas as pd, numpy as np, joblib, time, json
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

o = od("04_model_comparison"); md = o / "models"; md.mkdir(exist_ok=True)
d = pd.read_parquet(OUT / "03_feature_engineering" / "features.parquet")
features = [x for x in pd.read_csv(OUT / "03_feature_engineering" / "feature_list.csv").feature if x not in ("lag_7", "lag_14")]
dates = np.array(sorted(d.date.unique()))
CAP = {"Random Forest": 600000}
MODELS = ["Ridge Regression", "Random Forest", "XGBoost", "LightGBM"]


def make_model(name):
    if name == "Ridge Regression": return make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    if name == "Random Forest": return RandomForestRegressor(n_estimators=120, max_depth=18, min_samples_leaf=3, n_jobs=-1, random_state=SEED)
    if name == "XGBoost": return XGBRegressor(n_estimators=450, max_depth=8, learning_rate=.05, subsample=.8, colsample_bytree=.8, n_jobs=-1,
                                              random_state=SEED, objective="reg:squarederror", tree_method="hist")
    if name == "LightGBM": return LGBMRegressor(n_estimators=450, num_leaves=63, learning_rate=.05, subsample=.85, subsample_freq=1,
                                                colsample_bytree=.85, n_jobs=-1, random_state=SEED, verbosity=-1)


def fit(name, tr):
    if name in CAP and len(tr) > CAP[name]: tr = tr.sample(CAP[name], random_state=SEED)
    m = make_model(name); t = time.time(); m.fit(tr[features], tr.sales); return m, time.time() - t, len(tr)


def seasonal_naive(va):
    h = (va.date - va.date.min()).dt.days + 1
    return np.where(h <= 7, va.lag_7, np.where(h <= 14, va.lag_14, va.lag_21))


rows = []
for fi, end in enumerate([len(dates) - HORIZON * 4, len(dates) - HORIZON * 3, len(dates) - HORIZON * 2], 1):
    vd = dates[end:end + HORIZON]; tr = d[d.date < vd[0]]; va = d[d.date.isin(vd)]
    r = {"fold": fi, "model": "Seasonal Naive", "train_seconds": 0.0, "train_rows": 0}; r.update(metric(va.sales, seasonal_naive(va))); rows.append(r)
    for n in MODELS:
        m, sec, nr = fit(n, tr); r = {"fold": fi, "model": n, "train_seconds": sec, "train_rows": nr}
        r.update(metric(va.sales, np.clip(m.predict(va[features]), 0, None))); rows.append(r); print(fi, n, round(r["WAPE"], 5), f"{sec:.0f}s", flush=True)
cv = pd.DataFrame(rows); cv.to_csv(o / "rolling_cv_metrics.csv", index=False)
agg = cv.groupby("model").agg(WAPE_mean=("WAPE", "mean"), WAPE_std=("WAPE", "std"), MAE_mean=("MAE", "mean"), MAE_std=("MAE", "std"),
                              RMSE_mean=("RMSE", "mean"), RMSE_std=("RMSE", "std"), sMAPE_mean=("sMAPE", "mean"), RMSLE_mean=("RMSLE", "mean"),
                              train_seconds_mean=("train_seconds", "mean")).reset_index()
agg["rank_WAPE"] = agg.WAPE_mean.rank(method="min").astype(int)
agg = agg.sort_values(["WAPE_mean", "RMSE_mean", "MAE_mean"]).reset_index(drop=True)
winner = agg.iloc[0].model; agg["selected"] = agg.model.eq(winner); agg.to_csv(o / "model_comparison_summary.csv", index=False)

hold = dates[-HORIZON:]; tr = d[d.date < hold[0]]; te = d[d.date.isin(hold)].copy()
pred = pd.DataFrame({"date": te.date, "store_nbr": te.store_nbr, "family": te.family, "sales": te.sales, "onpromotion": te.onpromotion})
pred["Seasonal Naive"] = seasonal_naive(te)
final = [dict(model="Seasonal Naive", selected_by_cv=winner == "Seasonal Naive", **metric(te.sales, pred["Seasonal Naive"]))]
for n in MODELS:
    m, sec, nr = fit(n, tr); p = np.clip(m.predict(te[features]), 0, None); pred[n] = p
    joblib.dump(m, md / (n.lower().replace(" ", "_") + ".joblib"))
    final.append(dict(model=n, selected_by_cv=winner == n, train_seconds=sec, train_rows=nr, **metric(te.sales, p)))
pd.DataFrame(final).to_csv(o / "final_holdout_metrics.csv", index=False)
pred.to_parquet(o / "final_holdout_predictions.parquet", index=False)
save_json({"selection_metric": "mean WAPE across 3 rolling-origin CV folds", "tie_breakers": ["RMSE_mean", "MAE_mean"], "winner": winner,
           "final_holdout_used_for_selection": False, "final_holdout_days": HORIZON, "pipeline_version": "1.0"}, o / "model_selection.json")
(o / "best_model.txt").write_text(winner, encoding="utf-8")
if winner != "Seasonal Naive":
    joblib.dump(joblib.load(md / (winner.lower().replace(" ", "_") + ".joblib")), md / "selected_point_model.joblib")
lm = joblib.load(md / "lightgbm.joblib")
pd.DataFrame({"feature": features, "importance": lm.feature_importances_}).sort_values("importance", ascending=False).to_csv(o / "lightgbm_feature_importance.csv", index=False)
if winner == "XGBoost":
    xm = joblib.load(md / "xgboost.joblib"); gain = xm.get_booster().get_score(importance_type="gain")
    pd.DataFrame({"feature": features, "gain": [gain.get(f, 0.0) for f in features]}).sort_values("gain", ascending=False).to_csv(o / "selected_model_feature_importance.csv", index=False)
print("CV WINNER:", winner); print(agg.to_string(index=False))
