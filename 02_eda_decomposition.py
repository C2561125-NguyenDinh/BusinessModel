from src.common import *
import pandas as pd, matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import STL
d=load_train(); o=od("02_eda_decomposition"); fig=o/"figures";fig.mkdir(exist_ok=True)
daily=d.groupby("date",as_index=False).agg(sales=("sales","sum"),onpromotion=("onpromotion","sum"))
daily.to_csv(o/"daily_sales.csv",index=False)
promo=(d.assign(promo=d.onpromotion>0).groupby("promo",as_index=False)
       .agg(rows=("sales","size"),mean_sales=("sales","mean"),median_sales=("sales","median")))
promo.to_csv(o/"promotion_descriptive.csv",index=False)
s=daily.set_index("date").sales.asfreq("D").interpolate()
r=STL(s,period=7,robust=True).fit()
pd.DataFrame({"date":s.index,"observed":s.values,"trend":r.trend.values,
              "seasonal":r.seasonal.values,"resid":r.resid.values}).to_csv(o/"stl_weekly.csv",index=False)
plt.figure(figsize=(12,5));plt.plot(daily.date,daily.sales);plt.title("Favorita aggregate daily sales");plt.tight_layout();plt.savefig(fig/"daily_sales.png",dpi=150);plt.close()
f=r.plot();f.set_size_inches(12,8);f.tight_layout();f.savefig(fig/"robust_stl_weekly.png",dpi=150);plt.close(f)
print("EDA + Robust STL complete")
