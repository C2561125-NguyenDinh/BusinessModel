import numpy as np, pandas as pd
H=16
def build_features(d,horizon=H):
    x=d.copy().sort_values(["store_nbr","family","date"])
    dt=pd.to_datetime(x.date); x["dow"]=dt.dt.dayofweek; x["month"]=dt.dt.month; x["weekend"]=(x.dow>=5).astype(int)
    x["store_code"]=pd.Categorical(x.store_nbr).codes; x["family_code"]=pd.Categorical(x.family).codes
    g=x.groupby(["store_nbr","family"],sort=False).sales
    for lag in [horizon,horizon+7,horizon+14,35,42]: x[f"lag_{lag}"]=g.shift(lag)
    shifted=g.shift(horizon); sg=shifted.groupby([x.store_nbr,x.family],sort=False)
    for w in [7,14,28]: x[f"mean_{w}_s{horizon}"]=sg.transform(lambda z:z.rolling(w,min_periods=w).mean())
    x["std_28"]=sg.transform(lambda z:z.rolling(28,min_periods=28).std())
    feats=["onpromotion","dow","month","weekend","store_code","family_code",
           f"lag_{horizon}",f"lag_{horizon+7}",f"lag_{horizon+14}","lag_35","lag_42",
           f"mean_7_s{horizon}",f"mean_14_s{horizon}",f"mean_28_s{horizon}","std_28"]
    return x,feats
