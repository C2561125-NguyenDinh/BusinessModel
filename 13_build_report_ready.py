"""Stage 13: sinh REPORT_READY/tables (CSV) và REPORT_READY/figures (F01–F25) trực tiếp từ outputs/ của lần chạy."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.common import OUT, ROOT
SRC = OUT
DST = ROOT / "REPORT_READY"; TB = DST / "tables"; FG = DST / "figures"
TB.mkdir(parents=True, exist_ok=True); FG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": .25})
BLUE, GREY, RED, AMB, GRN = "#2563EB", "#A5B4FC", "#F04438", "#F79009", "#12B76A"
R = lambda p: pd.read_csv(SRC / p)
sel = json.load(open(SRC / "04_model_comparison/model_selection.json")); win = sel["winner"]


def save(name):
    plt.tight_layout(); plt.savefig(FG / name, bbox_inches="tight"); plt.close()


q = R("01_data_validation/data_quality.csv"); q.to_csv(TB / "01_data_quality.csv", index=False)
R("02_eda_decomposition/promotion_descriptive.csv").to_csv(TB / "02_promotion_descriptive.csv", index=False)
R("03_feature_engineering/feature_list.csv").to_csv(TB / "03_feature_list.csv", index=False)
cv = R("04_model_comparison/model_comparison_summary.csv"); cv.to_csv(TB / "05_model_cv_summary.csv", index=False)
fo = R("04_model_comparison/rolling_cv_metrics.csv"); fo.to_csv(TB / "06_rolling_cv_metrics.csv", index=False)
fh = R("04_model_comparison/final_holdout_metrics.csv"); fh.to_csv(TB / "07_final_holdout_metrics.csv", index=False)
cvh = cv[["model", "WAPE_mean"]].rename(columns={"WAPE_mean": "CV_WAPE"}).merge(fh[["model", "WAPE"]].rename(columns={"WAPE": "Holdout_WAPE"}), on="model")
cvh.to_csv(TB / "08_cv_vs_holdout.csv", index=False)
fi = R("04_model_comparison/lightgbm_feature_importance.csv"); fi.to_csv(TB / "09_feature_importance.csv", index=False)
day = R("11_forecast_diagnostics/actual_vs_predicted_by_day.csv"); day.to_csv(TB / "10_actual_predicted_by_day.csv", index=False)
dl = R("11_forecast_diagnostics/error_by_demand_level.csv"); dl.to_csv(TB / "11_error_by_demand_level.csv", index=False)
pm = R("05_probabilistic_forecast/probabilistic_metrics.csv"); pm.to_csv(TB / "12_probabilistic_metrics.csv", index=False)
pr = pd.read_parquet(SRC / "05_probabilistic_forecast/probabilistic_predictions.parquet")
pr["cov"] = (pr.sales >= pr.p10) & (pr.sales <= pr.p90); pr["w"] = pr.p90 - pr.p10
pf = pr.groupby("family").agg(coverage=("cov", "mean"), mean_width=("w", "mean"), mean_sales=("sales", "mean")).reset_index().sort_values("coverage")
pf.to_csv(TB / "13_probabilistic_by_family.csv", index=False)
ps = pr.groupby(["store_nbr", "family"]).agg(mean_sales=("sales", "mean"), mean_width=("w", "mean"), coverage=("cov", "mean")).reset_index(); ps.to_csv(TB / "14_probabilistic_by_series.csv", index=False)
R("06_promotion_scenarios/promotion_scenario_summary.csv").to_csv(TB / "15_promotion_scenario_summary.csv", index=False)
sens = R("12_case_studies/promotion_sensitivity_by_series.csv").sort_values("promotion_sensitivity_abs", ascending=False); sens.head(10).to_csv(TB / "16_top_promotion_sensitivity.csv", index=False)
R("07_inventory_decision/inventory_assumptions.csv").to_csv(TB / "17_inventory_assumptions.csv", index=False)
inv = R("07_inventory_decision/inventory_recommendations.csv")
inv.risk.value_counts().rename_axis("risk").reset_index(name="cases").to_csv(TB / "18_inventory_risk_counts.csv", index=False)
gs = SRC / "08_genai_decision_support/genai_run_status.csv"
if gs.exists(): pd.read_csv(gs).to_csv(TB / "19_genai_run_status.csv", index=False)
dq = SRC / "08_genai_decision_support/decision_queue.csv"
if dq.exists(): pd.read_csv(dq).head(20).to_csv(TB / "20_decision_queue_top20.csv", index=False)
cs = R("12_case_studies/case_study_index.csv"); cs.to_csv(TB / "21_representative_cases.csv", index=False)
R("11_forecast_diagnostics/error_by_store.csv").to_csv(TB / "error_by_store.csv", index=False)
R("11_forecast_diagnostics/error_by_family.csv").to_csv(TB / "error_by_family.csv", index=False)
cb = SRC / "05_probabilistic_forecast/conformal_bins.csv"
if cb.exists(): pd.read_csv(cb).to_csv(TB / "22_conformal_bins.csv", index=False)

# ------------------------------------------------------------------ figures
plt.figure(figsize=(7, 3.6)); v = [q.rows[0] / 1e6, q.stores[0], q.families[0], q.series[0] / 100]
b = plt.bar(["Quan sát (triệu)", "Cửa hàng", "Nhóm sản phẩm", "Chuỗi (trăm)"], v, color=[BLUE, GREY, GREY, BLUE])
for r_, lab in zip(b, [f"{q.rows[0]:,}".replace(",", "."), q.stores[0], q.families[0], f"{q.series[0]:,}".replace(",", ".")]):
    plt.text(r_.get_x() + r_.get_width() / 2, r_.get_height(), str(lab), ha="center", va="bottom")
plt.title("Quy mô dữ liệu Favorita"); save("F01_data_scale.png")
da = R("01_data_validation/daily_aggregate.csv"); da["date"] = pd.to_datetime(da.date)
plt.figure(figsize=(10, 3.6)); plt.plot(da.date, da.sales, lw=.6, color=GREY, label="Doanh số ngày"); plt.plot(da.date, da.sales.rolling(28, min_periods=7).mean(), color=BLUE, lw=1.8, label="TB trượt 28 ngày")
plt.legend(); plt.title("Tổng doanh số theo ngày"); save("F02_daily_sales.png")
w = da.assign(d=da.date.dt.dayofweek).groupby("d").sales.mean()
plt.figure(figsize=(6.5, 3.4)); plt.bar(["T2", "T3", "T4", "T5", "T6", "T7", "CN"], w.values, color=[GREY] * 5 + [BLUE] * 2); plt.title("Doanh số trung bình theo thứ trong tuần"); save("F03_weekday_pattern.png")
stl = R("02_eda_decomposition/stl_weekly.csv"); stl["date"] = pd.to_datetime(stl.date)
fig, ax = plt.subplots(4, 1, figsize=(10, 7.5), sharex=True)
for a_, c_, t_ in zip(ax, ["observed", "trend", "seasonal", "resid"], ["Quan sát", "Xu hướng", "Mùa vụ (7 ngày)", "Phần dư"]):
    a_.plot(stl.date, stl[c_], lw=.7 if c_ != "trend" else 1.6, color=BLUE if c_ == "trend" else "#344054"); a_.set_ylabel(t_)
fig.suptitle("Phân rã Robust STL (period = 7)"); save("F05_robust_stl.png")
r = cv.sort_values("WAPE_mean")
plt.figure(figsize=(7, 3.8)); plt.bar(r.model, r.WAPE_mean * 100, yerr=r.WAPE_std * 100, capsize=4, color=[BLUE if m == win else GREY for m in r.model])
for i, v in enumerate(r.WAPE_mean): plt.text(i, v * 100 + .3, f"{v*100:.2f}".replace(".", ","), ha="center")
plt.ylabel("WAPE trung bình (%)"); plt.title("WAPE trung bình qua 3 lần kiểm định (vạch: độ lệch chuẩn)"); plt.xticks(rotation=12); save("F06_cv_model_comparison.png")
plt.figure(figsize=(7, 3.8))
for m in r.model:
    x = fo[fo.model == m]; plt.plot(x.fold, x.WAPE * 100, marker="o", lw=2.2 if m == win else 1.2, label=m)
plt.xticks([1, 2, 3]); plt.xlabel("Lần kiểm định"); plt.ylabel("WAPE (%)"); plt.legend(fontsize=8); plt.title("WAPE theo từng lần kiểm định"); save("F07_fold_stability.png")
h = fh.sort_values("WAPE")
plt.figure(figsize=(7, 3.8)); plt.bar(h.model, h.WAPE * 100, color=[BLUE if m == win else GREY for m in h.model])
for i, v in enumerate(h.WAPE): plt.text(i, v * 100 + .2, f"{v*100:.2f}".replace(".", ","), ha="center")
plt.ylabel("WAPE (%)"); plt.title("WAPE trên tập kiểm tra cuối 16 ngày"); plt.xticks(rotation=12); save("F08_final_holdout.png")
x = cvh.sort_values("CV_WAPE"); i = np.arange(len(x))
plt.figure(figsize=(7.5, 3.8)); plt.bar(i - .2, x.CV_WAPE * 100, .4, color=BLUE, label="Kiểm định chéo"); plt.bar(i + .2, x.Holdout_WAPE * 100, .4, color=AMB, label="Tập kiểm tra cuối")
plt.xticks(i, x.model, rotation=12); plt.ylabel("WAPE (%)"); plt.legend(); plt.title("WAPE kiểm định chéo và tập kiểm tra cuối"); save("F09_cv_vs_holdout.png")
z = fi.head(20).iloc[::-1]
plt.figure(figsize=(7, 5.5)); plt.barh(z.feature, z.importance, color=BLUE); plt.xlabel("Số lần tách"); plt.title("20 đặc trưng có số lần tách lớn nhất — LightGBM đối chứng"); save("F10_feature_importance.png")
day["date"] = pd.to_datetime(day.date)
plt.figure(figsize=(9, 3.8)); plt.fill_between(day.date, day.p10, day.p90, color=BLUE, alpha=.15, label="Tổng P10–P90"); plt.plot(day.date, day.predicted, color=BLUE, lw=2, label="Dự báo P50")
plt.plot(day.date, day.actual, color="#101828", marker="o", ms=3, lw=1.2, label="Thực tế"); plt.legend(); plt.title("Tổng thực tế và dự báo theo ngày trên tập kiểm tra cuối"); save("F11_actual_vs_forecast_daily.png")
plt.figure(figsize=(5.2, 5)); plt.scatter(pr.sales + 1, pr.p50 + 1, s=2, alpha=.25, color=BLUE); mx = pr.sales.max() + 1
plt.plot([1, mx], [1, mx], "k--", lw=1); plt.xscale("log"); plt.yscale("log"); plt.xlabel("Thực tế + 1 (log)"); plt.ylabel("P50 + 1 (log)"); plt.title("Thực tế và dự báo ở cấp chuỗi – ngày"); save("F12_actual_predicted_scatter.png")
res = pr.sales - pr.p50; lo, hi = res.quantile([.01, .99])
plt.figure(figsize=(7, 3.6)); plt.hist(res.clip(lo, hi), bins=80, color=BLUE); plt.axvline(0, color="k", lw=1); plt.title("Phân phối phần dư (thực tế − P50), cắt ở phân vị 1% và 99%"); save("F13_residual_distribution.png")
plt.figure(figsize=(6, 4)); plt.scatter(pr.sales + 1, (pr.sales - pr.p50).abs() + 1, s=2, alpha=.25, color=BLUE); plt.xscale("log"); plt.yscale("log")
plt.xlabel("Thực tế + 1 (log)"); plt.ylabel("|Sai số| + 1 (log)"); plt.title("Sai số tuyệt đối theo quy mô nhu cầu"); save("F14_error_vs_demand.png")
es = R("11_forecast_diagnostics/error_by_store.csv").sort_values("WAPE", ascending=False).head(20).iloc[::-1]
plt.figure(figsize=(6.5, 5)); plt.barh("CH " + es.store_nbr.astype(str), es.WAPE * 100, color=BLUE); plt.xlabel("WAPE (%)"); plt.title("20 cửa hàng có WAPE cao nhất"); save("F15_wape_by_store.png")
ef = R("11_forecast_diagnostics/error_by_family.csv").sort_values("WAPE", ascending=False).head(20).iloc[::-1]
plt.figure(figsize=(7, 5.2)); plt.barh(ef.family, ef.WAPE * 100, color=BLUE); plt.xscale("log"); plt.xlabel("WAPE (%, thang log)"); plt.title("20 nhóm sản phẩm có WAPE cao nhất"); save("F16_wape_by_family.png")
plt.figure(figsize=(6.5, 3.6)); ax1 = plt.gca(); ax1.bar(dl.demand_level, dl.WAPE * 100, color=BLUE); ax1.set_ylabel("WAPE (%)"); ax1.set_yscale("log")
ax2 = ax1.twinx(); ax2.plot(dl.demand_level, dl.coverage_P10_P90 * 100, color=RED, marker="o", lw=2); ax2.set_ylabel("Bao phủ P10–P90 (%)", color=RED); ax2.set_ylim(0, 105); ax2.axhline(80, color=RED, ls=":", lw=1)
plt.title("WAPE (cột) và độ bao phủ (đường) theo mức nhu cầu"); save("F17_error_by_demand_level.png")
m = pm.iloc[0]
plt.figure(figsize=(5.5, 3.4)); plt.bar(["P10", "P50", "P90"], [m.Pinball_P10, m.Pinball_P50, m.Pinball_P90], color=[GREY, BLUE, GREY]); plt.title("Pinball loss theo phân vị"); save("F18_pinball_loss.png")
plt.figure(figsize=(7, 6)); plt.barh(pf.family, pf.coverage * 100, color=[RED if c < .7 else (AMB if c < .8 else GRN) for c in pf.coverage]); plt.axvline(80, color="k", ls="--", lw=1)
plt.xlabel("Độ bao phủ P10–P90 (%)"); plt.title("Độ bao phủ theo nhóm sản phẩm (đường nét đứt: 80%)"); save("F19_coverage_by_family.png")
plt.figure(figsize=(6, 4)); plt.scatter(ps.mean_sales + 1, ps.mean_width, s=6, alpha=.5, color=BLUE); plt.xscale("log"); plt.yscale("log")
plt.xlabel("Doanh số TB/ngày + 1 (log)"); plt.ylabel("Độ rộng TB P10–P90 (log)"); plt.title("Độ rộng khoảng theo quy mô chuỗi"); save("F20_interval_width_vs_demand.png")
sc = R("06_promotion_scenarios/promotion_scenario_summary.csv").set_index("scenario").reindex(["No promotion", "Low", "Current", "Medium", "High"])
plt.figure(figsize=(6.5, 3.6)); plt.bar(sc.index, sc.p50_mean, color=[GREY, GREY, BLUE, GREY, GREY]); plt.ylabel("P50 trung bình mỗi chuỗi (16 ngày)"); plt.title("P50 trung bình theo kịch bản khuyến mãi"); save("F21_promotion_scenarios.png")
t = sens.head(20).iloc[::-1]
plt.figure(figsize=(7, 5.2)); plt.barh("CH " + t.store_nbr.astype(str) + " – " + t.family, t.promotion_sensitivity_abs, color=BLUE); plt.xlabel("|P50 KM cao − P50 hiện tại|"); plt.title("20 chuỗi nhạy nhất với kịch bản khuyến mãi"); save("F22_promotion_sensitivity.png")
rk = inv.risk.value_counts().reindex(["HIGH", "MEDIUM", "LOW"]).fillna(0)
plt.figure(figsize=(5.5, 3.4)); plt.bar(rk.index, rk.values, color=[RED, AMB, GRN])
for i_, v in enumerate(rk.values): plt.text(i_, v, f"{int(v):,}".replace(",", "."), ha="center", va="bottom")
plt.title("Số chuỗi theo nhãn rủi ro tồn kho"); save("F23_inventory_risk.png")
plt.figure(figsize=(6.5, 3.6)); x = inv.suggested_replenishment; plt.hist(x[x <= x.quantile(.99)], bins=60, color=BLUE); plt.xlabel("Lượng bổ sung gợi ý (≤ phân vị 99)"); plt.title("Phân phối lượng bổ sung gợi ý"); save("F24_replenishment_distribution.png")
for _, c in cs.iterrows():
    x = pr[(pr.store_nbr == c.store_nbr) & (pr.family == c.family)].sort_values("date"); x["date"] = pd.to_datetime(x.date)
    fig, ax = plt.subplots(2, 1, figsize=(8, 5), sharex=True, gridspec_kw=dict(height_ratios=[3, 1.2]))
    ax[0].fill_between(x.date, x.p10, x.p90, color=BLUE, alpha=.18, label="P10–P90"); ax[0].plot(x.date, x.p50, color=BLUE, lw=2, label="P50"); ax[0].plot(x.date, x.sales, color="#101828", marker="o", ms=3, label="Thực tế")
    ax[0].legend(fontsize=8); ax[0].set_title(f"{c.case}: CH {c.store_nbr} – {c.family}")
    ax[1].bar(x.date, x.sales - x.p50, color=[GRN if v >= 0 else RED for v in x.sales - x.p50]); ax[1].set_ylabel("Phần dư")
    save(f"F25_case_{c.case}.png")
print("report ready", len(list(FG.glob("*.png"))), "figures", len(list(TB.glob("*.csv"))), "tables")
