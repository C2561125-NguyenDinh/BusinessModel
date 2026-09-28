from src.common import *
import pandas as pd, numpy as np
import matplotlib.pyplot as plt

o=od("11_forecast_diagnostics"); figs=o/"figures"; figs.mkdir(exist_ok=True)
sel=json.loads((OUT/"04_model_comparison"/"model_selection.json").read_text(encoding="utf-8")); winner=sel["winner"]
pt=pd.read_parquet(OUT/"04_model_comparison"/"final_holdout_predictions.parquet")
pr=pd.read_parquet(OUT/"05_probabilistic_forecast"/"probabilistic_predictions.parquet")
d=pt.merge(pr[["date","store_nbr","family","p10","p50","p90"]],on=["date","store_nbr","family"],how="left")
d["pred"]=d[winner] if winner in d.columns else d["p50"]
d["error"]=d.sales-d.pred; d["abs_error"]=d.error.abs(); d["sq_error"]=d.error**2
d["covered"]=(d.sales>=d.p10)&(d.sales<=d.p90); d["interval_width"]=d.p90-d.p10

def group_metrics(keys):
    def f(x):
        return pd.Series({"n":len(x),"actual_sum":x.sales.sum(),"pred_sum":x.pred.sum(),"MAE":x.abs_error.mean(),
            "RMSE":np.sqrt(x.sq_error.mean()),"WAPE":x.abs_error.sum()/(x.sales.abs().sum()+1e-9),
            "bias":x.error.mean(),"coverage_P10_P90":x.covered.mean(),"mean_interval_width":x.interval_width.mean()})
    return d.groupby(keys,observed=True).apply(f).reset_index()

group_metrics(["store_nbr"]).to_csv(o/"error_by_store.csv",index=False)
group_metrics(["family"]).to_csv(o/"error_by_family.csv",index=False)
series=group_metrics(["store_nbr","family"]); series.to_csv(o/"error_by_series.csv",index=False)
d.groupby("date",as_index=False).agg(actual=("sales","sum"),predicted=("pred","sum"),p10=("p10","sum"),p50=("p50","sum"),p90=("p90","sum"),MAE=("abs_error","mean")).to_csv(o/"actual_vs_predicted_by_day.csv",index=False)
# Demand-level diagnostics based on actual sales quantiles.
try: d["demand_level"]=pd.qcut(d.sales.rank(method="first"),4,labels=["Q1 thấp","Q2","Q3","Q4 cao"])
except Exception: d["demand_level"]="Tất cả"
group_metrics(["demand_level"]).to_csv(o/"error_by_demand_level.csv",index=False)
# Representative cases selected mechanically, not manually.
elig=series[series.actual_sum>series.actual_sum.quantile(.25)].copy()
cases=[]
if len(elig):
    cases.append(("du_bao_tot",elig.sort_values("WAPE").iloc[0]))
    cases.append(("du_bao_kho",elig.sort_values("WAPE",ascending=False).iloc[0]))
    cases.append(("bat_dinh_cao",elig.sort_values("mean_interval_width",ascending=False).iloc[0]))
pd.DataFrame([{"case":k,**r.to_dict()} for k,r in cases]).to_csv(o/"representative_cases.csv",index=False)
# Figures from actual project outputs.
plt.figure(figsize=(10,5)); a=d.groupby("date",as_index=False).agg(actual=("sales","sum"),pred=("pred","sum")); plt.plot(a.date,a.actual,label="Thực tế"); plt.plot(a.date,a.pred,label=f"Dự báo {winner}"); plt.legend(); plt.title("Tổng nhu cầu thực tế và dự báo trên tập kiểm tra cuối"); plt.xticks(rotation=30); plt.tight_layout(); plt.savefig(figs/"01_actual_vs_predicted_total.png",dpi=180); plt.close()
plt.figure(figsize=(6,6)); sample=d.sample(min(25000,len(d)),random_state=SEED); plt.scatter(sample.sales,sample.pred,s=5,alpha=.18); lim=max(sample.sales.max(),sample.pred.max()); plt.plot([0,lim],[0,lim]); plt.xlabel("Thực tế"); plt.ylabel("Dự báo"); plt.title("Thực tế so với dự báo"); plt.tight_layout(); plt.savefig(figs/"02_actual_vs_predicted_scatter.png",dpi=180); plt.close()
plt.figure(figsize=(9,5)); lo,hi=np.quantile(d.error,[.01,.99]); plt.hist(d.error.clip(lo,hi),bins=80); plt.axvline(0); plt.xlabel("Sai số = thực tế - dự báo"); plt.title("Phân phối sai số dự báo (cắt 1% hai đuôi để hiển thị)"); plt.tight_layout(); plt.savefig(figs/"03_residual_distribution.png",dpi=180); plt.close()
for name,r in cases:
    x=d[(d.store_nbr==r.store_nbr)&(d.family==r.family)].sort_values("date")
    plt.figure(figsize=(10,5)); plt.fill_between(x.date,x.p10,x.p90,alpha=.18,label="P10–P90"); plt.plot(x.date,x.sales,marker='o',label="Thực tế"); plt.plot(x.date,x.p50,marker='o',label="P50"); plt.title(f"Case {name}: Store {int(r.store_nbr)} × {r.family}"); plt.legend(); plt.xticks(rotation=30); plt.tight_layout(); plt.savefig(figs/f"case_{name}.png",dpi=180); plt.close()
print("FORECAST DIAGNOSTICS: PASS", winner, "| cases:", len(cases))
