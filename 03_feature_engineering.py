"""Stage 03: tạo đặc trưng an toàn rò rỉ cho kỳ dự báo trực tiếp 16 ngày.

Nguyên tắc thiết kế:
  1) Hoàn thiện lịch ngày cho mọi chuỗi (thêm các ngày 25/12 cửa hàng đóng cửa, sales = 0) để lag/rolling
     là độ trễ theo NGÀY LỊCH, không phải theo dòng. Các ngày đóng cửa không đưa vào huấn luyện/đánh giá.
  2) Giá dầu: điền tiến trên lịch ngày rồi dịch 16 NGÀY LỊCH.
  3) Giao dịch: dịch/trượt trên lịch ngày của TỪNG cửa hàng rồi mới ghép vào bảng chuỗi.
  4) Ngày lễ quốc gia: loại type = "Work Day" (ngày làm bù) và ngày đã chuyển (transferred).
"""
from src.common import *
import pandas as pd, numpy as np

d = load_train(); o = od("03_feature_engineering")
cal = pd.date_range(d.date.min(), d.date.max(), freq="D")
idx = pd.MultiIndex.from_product([sorted(d.store_nbr.unique()), sorted(d.family.unique()), cal], names=["store_nbr", "family", "date"])
d = d.set_index(["store_nbr", "family", "date"])[["sales", "onpromotion"]].reindex(idx).reset_index()
d["closed"] = d.sales.isna().astype("int8"); d[["sales", "onpromotion"]] = d[["sales", "onpromotion"]].fillna(0)
g = d.groupby(["store_nbr", "family"], sort=False)["sales"]
for lag in [7, 14, 16, 21, 28, 32, 35, 42, 56]:
    d[f"lag_{lag}"] = g.shift(lag)
for win in [7, 14, 28]:
    d[f"roll_mean_{win}"] = g.transform(lambda s: s.shift(HORIZON).rolling(win).mean())
    d[f"roll_std_{win}"] = g.transform(lambda s: s.shift(HORIZON).rolling(win).std())
d["dow"] = d.date.dt.dayofweek; d["month"] = d.date.dt.month; d["day"] = d.date.dt.day
d["weekofyear"] = d.date.dt.isocalendar().week.astype("int16"); d["is_weekend"] = (d.dow >= 5).astype("int8")
d["store_code"] = d.store_nbr.astype("int16"); d["family_code"] = pd.Categorical(d.family).codes.astype("int16")
features = ["onpromotion", "dow", "month", "day", "weekofyear", "is_weekend", "store_code", "family_code",
            "lag_7", "lag_14", "lag_16", "lag_21", "lag_28", "lag_32", "lag_35", "lag_42", "lag_56",
            "roll_mean_7", "roll_mean_14", "roll_mean_28", "roll_std_7", "roll_std_14", "roll_std_28"]
used = []
s = pd.read_csv(RAW / "stores.csv").drop_duplicates("store_nbr")
for c in ["city", "state", "type"]:
    s[c + "_code"] = pd.Categorical(s[c]).codes.astype("int16")
d = d.merge(s[["store_nbr", "city_code", "state_code", "type_code", "cluster"]], on="store_nbr", how="left")
features += ["city_code", "state_code", "type_code", "cluster"]; used.append("stores.csv: static store metadata")
oil = pd.read_csv(RAW / "oil.csv", parse_dates=["date"]).sort_values("date")
oc = pd.DataFrame({"date": pd.date_range(min(oil.date.min(), d.date.min()), d.date.max(), freq="D")}).merge(oil, on="date", how="left")
oc["dcoilwtico"] = oc.dcoilwtico.ffill().bfill(); oc["oil_price_lag16"] = oc.dcoilwtico.shift(HORIZON).bfill()
d = d.merge(oc[["date", "oil_price_lag16"]], on="date", how="left")
features.append("oil_price_lag16"); used.append("oil.csv: oil price lagged 16 calendar days")
t = pd.read_csv(RAW / "transactions.csv", parse_dates=["date"]).sort_values(["store_nbr", "date"])
parts = []
for sn, x in t.groupby("store_nbr"):
    x = x.set_index("date")[["transactions"]].reindex(cal)
    x["transactions_lag16"] = x.transactions.shift(HORIZON)
    x["transactions_roll28_lag16"] = x.transactions.shift(HORIZON).rolling(28, min_periods=7).mean()
    x[["transactions_lag16", "transactions_roll28_lag16"]] = x[["transactions_lag16", "transactions_roll28_lag16"]].ffill()
    x["store_nbr"] = sn; parts.append(x.rename_axis("date").reset_index()[["date", "store_nbr", "transactions_lag16", "transactions_roll28_lag16"]])
d = d.merge(pd.concat(parts), on=["date", "store_nbr"], how="left")
features += ["transactions_lag16", "transactions_roll28_lag16"]; used.append("transactions.csv: store transactions lagged 16 calendar days")
h = pd.read_csv(RAW / "holidays_events.csv", parse_dates=["date"])
h = h[h.locale.astype(str).str.lower().eq("national") & ~h.transferred.astype(str).str.lower().eq("true") & (h["type"] != "Work Day")]
d = d.merge(pd.DataFrame({"date": h.date.drop_duplicates(), "is_national_holiday": 1}), on="date", how="left")
d["is_national_holiday"] = d.is_national_holiday.fillna(0).astype("int8")
features.append("is_national_holiday"); used.append("holidays_events.csv: national holidays (not transferred, excluding Work Day)")
z = d.dropna(subset=features); z = z[z.closed == 0].copy()
z.to_parquet(o / "features.parquet", index=False)
pd.DataFrame({"feature": features}).to_csv(o / "feature_list.csv", index=False)
pd.DataFrame({"optional_source": used, "rule": ["known/static or lagged >=16 calendar days"] * len(used)}).to_csv(o / "optional_features_used.csv", index=False)
print("Feature rows:", len(z), "| dates:", z.date.nunique(), "| first:", z.date.min().date())
