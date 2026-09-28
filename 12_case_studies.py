from src.common import *
import pandas as pd, numpy as np

o=od("12_case_studies")
err=pd.read_csv(OUT/"11_forecast_diagnostics"/"error_by_series.csv")
rep=pd.read_csv(OUT/"11_forecast_diagnostics"/"representative_cases.csv")
ps=pd.read_csv(OUT/"06_promotion_scenarios"/"promotion_scenarios.csv")
piv=ps.pivot_table(index=["store_nbr","family"],columns="scenario",values="p50",aggfunc="first").reset_index()
if "Current" in piv.columns:
    for c in ["No promotion","Low","Medium","High"]:
        if c in piv.columns: piv[f"delta_{c}_vs_current"]=piv[c]-piv["Current"]
    if "High" in piv.columns: piv["promotion_sensitivity_abs"]=abs(piv["High"]-piv["Current"])
piv.to_csv(o/"promotion_sensitivity_by_series.csv",index=False)
# Add one mechanically selected high-sensitivity case to the research case list.
if "promotion_sensitivity_abs" in piv.columns and len(piv):
    s=piv.sort_values("promotion_sensitivity_abs",ascending=False).iloc[0]
    extra=pd.DataFrame([{"case":"nhay_khuyen_mai","store_nbr":s.store_nbr,"family":s.family}])
    rep=pd.concat([rep,extra],ignore_index=True,sort=False)
rep.to_csv(o/"case_study_index.csv",index=False)
# Machine-readable notes for report generation; no invented interpretation.
notes=[]
for _,r in rep.iterrows():
    m=err[(err.store_nbr==r.store_nbr)&(err.family==r.family)]
    if len(m):
        x=m.iloc[0]; notes.append({"case":r['case'],"store_nbr":r.store_nbr,"family":r.family,"WAPE":x.WAPE,"MAE":x.MAE,"RMSE":x.RMSE,"bias":x.bias,"coverage_P10_P90":x.coverage_P10_P90,"mean_interval_width":x.mean_interval_width})
pd.DataFrame(notes).to_csv(o/"case_study_metrics.csv",index=False)
print("CASE STUDIES: PASS", len(rep))
