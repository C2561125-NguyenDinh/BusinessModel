"""Nạp đầu ra của pipeline và lọc theo phạm vi (cửa hàng, nhóm hàng, nhãn rủi ro)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

FILES = {
    "quality": "01_data_validation/data_quality.csv",
    "cv_summary": "04_model_comparison/model_comparison_summary.csv",
    "cv_folds": "04_model_comparison/rolling_cv_metrics.csv",
    "holdout": "04_model_comparison/final_holdout_metrics.csv",
    "importance": "04_model_comparison/selected_model_feature_importance.csv",
    "prob_metrics": "05_probabilistic_forecast/probabilistic_metrics.csv",
    "bins": "05_probabilistic_forecast/conformal_bins.csv",
    "pred": "05_probabilistic_forecast/probabilistic_predictions.parquet",
    "scen": "06_promotion_scenarios/promotion_scenarios.csv",
    "scen_summary": "06_promotion_scenarios/promotion_scenario_summary.csv",
    "inv": "07_inventory_decision/inventory_recommendations.csv",
    "inv_assump": "07_inventory_decision/inventory_assumptions.csv",
    "queue": "08_genai_decision_support/decision_queue.csv",
    "genai_status": "08_genai_decision_support/genai_run_status.csv",
    "err_series": "11_forecast_diagnostics/error_by_series.csv",
    "err_level": "11_forecast_diagnostics/error_by_demand_level.csv",
    "selection": "04_model_comparison/model_selection.json",
    "cases": "08_genai_decision_support/decision_cases.jsonl",
}
SERIES_KEYS = ["store_nbr", "family"]


@dataclass
class Scope:
    stores: list = field(default_factory=list)      # rỗng = tất cả
    families: list = field(default_factory=list)
    risks: list = field(default_factory=list)

    def label(self) -> str:
        def one(v, allname):
            if not v:
                return allname
            v = [str(x) for x in v]
            return ", ".join(v[:6]) + (f" (+{len(v) - 6})" if len(v) > 6 else "")
        return (f"Cửa hàng: {one(self.stores, 'tất cả 54')} · Nhóm hàng: {one(self.families, 'tất cả 33')}"
                f" · Nhãn rủi ro: {one(self.risks, 'tất cả')}")

    def is_all(self) -> bool:
        return not (self.stores or self.families or self.risks)


def _read(out: Path, rel: str):
    p = Path(out) / rel
    if not p.exists():
        return None
    if rel.endswith(".parquet"):
        return pd.read_parquet(p)
    if rel.endswith(".json"):
        return json.loads(p.read_text(encoding="utf-8"))
    if rel.endswith(".jsonl"):
        return [json.loads(z) for z in p.read_text(encoding="utf-8").splitlines() if z.strip()]
    return pd.read_csv(p)


def load_bundle(out: Path, with_cases: bool = False) -> dict:
    b = {k: _read(out, v) for k, v in FILES.items() if k != "cases" or with_cases}
    if b.get("pred") is not None:
        b["pred"]["date"] = pd.to_datetime(b["pred"]["date"])
    return b


def series_in_scope(b: dict, sc: Scope) -> pd.DataFrame:
    """Danh sách chuỗi (store_nbr, family) thuộc phạm vi; nhãn rủi ro lấy từ Stage 07."""
    inv = b["inv"][SERIES_KEYS + ["risk"]].copy()
    if sc.stores:
        inv = inv[inv.store_nbr.isin([int(s) for s in sc.stores])]
    if sc.families:
        inv = inv[inv.family.isin(sc.families)]
    if sc.risks:
        inv = inv[inv.risk.isin(sc.risks)]
    return inv[SERIES_KEYS]


def apply_scope(df: pd.DataFrame | None, keys: pd.DataFrame) -> pd.DataFrame | None:
    if df is None:
        return None
    if not set(SERIES_KEYS).issubset(df.columns):
        return df
    return df.merge(keys, on=SERIES_KEYS, how="inner")


def scope_metrics(b: dict, keys: pd.DataFrame) -> dict:
    """Chỉ số của phạm vi, tính lại trực tiếp từ dự báo tập kiểm tra cuối (Stage 05)."""
    p = apply_scope(b["pred"], keys)
    y, pt = p.sales.to_numpy(), p.point.to_numpy()
    ins = ((p.sales >= p.p10) & (p.sales <= p.p90)).mean() if len(p) else float("nan")
    inv = apply_scope(b["inv"], keys)
    return {
        "series": int(len(keys)),
        "rows": int(len(p)),
        "actual_sum": float(y.sum()),
        "point_sum": float(pt.sum()),
        "p50_sum": float(p.p50.sum()),
        "WAPE": float(abs(y - pt).sum() / y.sum()) if y.sum() > 0 else float("nan"),
        "coverage": float(ins),
        "width": float((p.p90 - p.p10).mean()) if len(p) else float("nan"),
        "risk_counts": inv.risk.value_counts().reindex(["HIGH", "MEDIUM", "LOW"]).fillna(0).astype(int).to_dict(),
        "replenishment_sum": float(inv.suggested_replenishment.sum()),
        "period": (p.date.min().date().isoformat(), p.date.max().date().isoformat()) if len(p) else ("", ""),
    }
