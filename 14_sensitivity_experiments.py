"""Stage 14: thí nghiệm độ nhạy của hai lựa chọn thiết kế trên đúng 3 lần kiểm định chéo của Stage 04.

  (a) XGBoost huấn luyện trên mẫu ngẫu nhiên 600.000 dòng thay vì toàn bộ dữ liệu huấn luyện.
  (b) LightGBM không đặt subsample_freq (khi đó subsample = 0,85 không có hiệu lực trong LightGBM).
Mọi thiết lập khác giữ nguyên như Stage 04. Kết quả: outputs/14_sensitivity/sensitivity_cv.csv
"""
from src.common import *
import time
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

o = od("14_sensitivity")
d = pd.read_parquet(OUT / "03_feature_engineering" / "features.parquet")
features = [x for x in pd.read_csv(OUT / "03_feature_engineering" / "feature_list.csv").feature if x not in ("lag_7", "lag_14")]
dates = np.array(sorted(d.date.unique()))


def xgb():
    return XGBRegressor(n_estimators=450, max_depth=8, learning_rate=.05, subsample=.8, colsample_bytree=.8, n_jobs=-1,
                        random_state=SEED, objective="reg:squarederror", tree_method="hist")


def lgb_no_freq():
    return LGBMRegressor(n_estimators=450, num_leaves=63, learning_rate=.05, subsample=.85, colsample_bytree=.85,
                         n_jobs=-1, random_state=SEED, verbosity=-1)


CONFIGS = [("XGBoost · mẫu 600.000 dòng", xgb, 600000), ("LightGBM · không đặt subsample_freq", lgb_no_freq, None)]
rows = []
for fi, end in enumerate([len(dates) - HORIZON * 4, len(dates) - HORIZON * 3, len(dates) - HORIZON * 2], 1):
    vd = dates[end:end + HORIZON]; tr = d[d.date < vd[0]]; va = d[d.date.isin(vd)]
    for name, mk, cap in CONFIGS:
        t = tr.sample(cap, random_state=SEED) if cap and len(tr) > cap else tr
        m = mk(); t0 = time.time(); m.fit(t[features], t.sales)
        r = {"fold": fi, "config": name, "train_rows": len(t), "train_seconds": time.time() - t0}
        r.update(metric(va.sales, np.clip(m.predict(va[features]), 0, None))); rows.append(r)
        print(fi, name, round(r["WAPE"], 5), flush=True)
res = pd.DataFrame(rows)
cv = pd.read_csv(OUT / "04_model_comparison" / "rolling_cv_metrics.csv")
base = cv[cv.model.isin(["XGBoost", "LightGBM"])].assign(config=lambda x: x.model + " · cấu hình chính thức")
res = pd.concat([base[["fold", "config", "train_rows", "train_seconds", "MAE", "RMSE", "WAPE", "sMAPE", "RMSLE"]], res], ignore_index=True)
res.to_csv(o / "sensitivity_cv.csv", index=False)
print(res.groupby("config").WAPE.mean())
