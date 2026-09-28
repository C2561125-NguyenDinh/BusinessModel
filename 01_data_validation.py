from src.common import *
import pandas as pd
d=load_train(); o=od("01_data_validation")
summary=pd.DataFrame([{
 "rows":len(d),"date_min":d.date.min(),"date_max":d.date.max(),
 "stores":d.store_nbr.nunique(),"families":d.family.nunique(),
 "series":len(d[["store_nbr","family"]].drop_duplicates()),
 "missing_sales":int(d.sales.isna().sum()),"missing_onpromotion":int(d.onpromotion.isna().sum()),
 "duplicates":int(d.duplicated(["date","store_nbr","family"]).sum()),
 "zero_sales_share":float((d.sales==0).mean()),
 "promotion_row_share":float((d.onpromotion>0).mean())}])
summary.to_csv(o/"data_quality.csv",index=False)
d.groupby("date",as_index=False).agg(sales=("sales","sum"),onpromotion=("onpromotion","sum")).to_csv(o/"daily_aggregate.csv",index=False)
print(summary.to_string(index=False))
