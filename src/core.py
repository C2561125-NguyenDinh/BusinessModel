from pathlib import Path
import json, hashlib, random, numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def paths():
    return {k:ROOT/k for k in ["data","artifacts","reports","logs","knowledge_base"]}
def seed_all(seed=42):
    random.seed(seed); np.random.seed(seed)
def fingerprint(files):
    h=hashlib.sha256()
    for f in files:
        p=Path(f)
        if p.exists():
            h.update(p.name.encode()); h.update(str(p.stat().st_size).encode()); h.update(str(p.stat().st_mtime_ns).encode())
    return h.hexdigest()[:16]
def save_json(path,obj):
    Path(path).parent.mkdir(parents=True,exist_ok=True); Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
