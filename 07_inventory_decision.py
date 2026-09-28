from src.common import *
import pandas as pd, numpy as np
p=pd.read_parquet(OUT/"05_probabilistic_forecast"/"probabilistic_predictions.parquet");o=od("07_inventory_decision")
a=p.groupby(["store_nbr","family"],as_index=False).agg(p10=("p10","sum"),p50=("p50","sum"),p90=("p90","sum"))
# Transparent scenario assumptions, because Favorita does not contain true inventory/lead time/cost.
Cu,Co=3.0,1.0;q=Cu/(Cu+Co)
a["critical_fractile"]=q;a["assumed_inventory_position"]=0.8*a.p50
a["reorder_point_proxy"]=a.p90 if q>=.75 else a.p50
a["safety_stock_proxy"]=np.maximum(a.reorder_point_proxy-a.p50,0)
a["suggested_replenishment"]=np.maximum(a.reorder_point_proxy-a.assumed_inventory_position,0)
a["risk"]=pd.cut((a.p90-a.p10)/(a.p50+1),[-np.inf,.35,.75,np.inf],labels=["LOW","MEDIUM","HIGH"]).astype(str)
a.to_csv(o/"inventory_recommendations.csv",index=False)
pd.DataFrame([{"Cu_assumption":Cu,"Co_assumption":Co,"q_star":q,"note":"Scenario only; no actual Favorita inventory/lead-time data."}]).to_csv(o/"inventory_assumptions.csv",index=False)
print(a.risk.value_counts())
