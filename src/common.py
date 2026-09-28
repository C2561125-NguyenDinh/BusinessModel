from pathlib import Path
import json, pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs"
RAW=ROOT/"data"/"raw"
HORIZON=16
SEED=42
def od(stage):
    p=OUT/stage; p.mkdir(parents=True,exist_ok=True); return p
def load_train():
    p=RAW/"train.csv"
    if not p.exists() and (RAW/"train.csv.gz").exists(): p=RAW/"train.csv.gz"   # bản nén trên GitHub
    if not p.exists(): raise FileNotFoundError(f"Missing {p}")
    d=pd.read_csv(p,parse_dates=["date"])
    need={"date","store_nbr","family","sales","onpromotion"}
    if not need.issubset(d.columns): raise ValueError(f"Wrong dataset/schema. Need {sorted(need)}")
    d=d.sort_values(["store_nbr","family","date"]).reset_index(drop=True)
    return d
def save_json(obj,path):
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
def metric(y,p):
    y=np.asarray(y,float);p=np.clip(np.asarray(p,float),0,None)
    e=y-p
    return {"MAE":float(np.mean(np.abs(e))),
            "RMSE":float(np.sqrt(np.mean(e**2))),
            "WAPE":float(np.sum(np.abs(e))/(np.sum(np.abs(y))+1e-9)),
            "sMAPE":float(np.mean(2*np.abs(e)/(np.abs(y)+np.abs(p)+1e-9))),
            "RMSLE":float(np.sqrt(np.mean((np.log1p(np.clip(y,0,None))-np.log1p(p))**2)))}
