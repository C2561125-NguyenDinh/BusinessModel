from pathlib import Path
import pandas as pd, numpy as np
from src.core import ROOT, seed_all
def detect_schema(df):
    cols=set(df.columns)
    if {"date","store_nbr","family","sales","onpromotion"}<=cols:return "store_sales"
    if {"date","store_nbr","item_nbr","unit_sales"}<=cols:return "favorita_2017"
    return "unknown"
def synthetic(seed=42, stores=4, families=8, days=620):
    seed_all(seed); rng=np.random.default_rng(seed)
    dates=pd.date_range("2015-01-01",periods=days)
    rows=[]
    for s in range(1,stores+1):
      for j in range(families):
        fam=f"FAMILY_{j+1:02d}"; base=8+2*j+rng.random()*4
        for i,d in enumerate(dates):
          promo=int(rng.random()<.13)*int(rng.integers(1,8))
          weekly=1+0.20*np.sin(2*np.pi*d.dayofweek/7)
          trend=1+0.0007*i
          shock=1.0
          if 470<=i<=485: shock=1.65
          mu=max(.1,base*weekly*trend*shock*(1+.035*promo))
          sales=float(rng.poisson(mu))
          if rng.random()<.07:sales=0.0
          rows.append((d,s,fam,sales,promo))
    return pd.DataFrame(rows,columns=["date","store_nbr","family","sales","onpromotion"])
def load_real(raw):
    p=Path(raw)/"train.csv"
    if not p.exists(): raise FileNotFoundError("Thiếu train.csv. Dùng --mode synthetic để kiểm thử.")
    d=pd.read_csv(p,parse_dates=["date"])
    sch=detect_schema(d)
    if sch=="favorita_2017": raise ValueError("Phát hiện bộ Favorita 2017 (item_nbr/unit_sales), không phải Store Sales schema.")
    if sch!="store_sales": raise ValueError("Schema train.csv không hợp lệ.")
    if d.duplicated(["date","store_nbr","family"]).any(): raise ValueError("Có khóa date-store-family trùng.")
    return d
