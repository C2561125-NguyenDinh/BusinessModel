from src.data.io import synthetic,detect_schema
from src.features.build import build_features
from src.inventory.policy import newsvendor_quantile,inventory_decision
from src.genai.rag import retrieve
from pathlib import Path
def test_schema_and_synthetic():
 d=synthetic(days=100); assert detect_schema(d)=="store_sales"; assert (d.sales>=0).all()
def test_leakage_lag():
 d=synthetic(stores=1,families=1,days=100); x,f=build_features(d,16)
 row=x.iloc[60]; assert row["lag_16"]==x.iloc[44].sales
def test_inventory():
 assert abs(newsvendor_quantile(3,1)-.75)<1e-9
 r=inventory_decision([10,20,30,40],5,3,1); assert r["suggested_replenishment"]>=0
def test_quantile_sort_fixture():
 import numpy as np
 a=np.sort(np.array([[3,1,2]]),axis=1); assert list(a[0])==[1,2,3]
