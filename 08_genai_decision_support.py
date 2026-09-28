"""Stage 08 — Trung tâm quyết định: phiếu khuyến nghị có căn cứ + RAG + GenAI (tùy chọn) + HITL.

  * Tạo phiếu cho TẤT CẢ chuỗi và xếp hàng đợi theo điểm ưu tiên minh bạch (reason codes).
  * Phiếu khuyến nghị chuẩn hóa: tóm tắt điều hành, 3 phương án số lượng (P50 / q* / P90), khuyến nghị
    khuyến mãi có cảnh báo ngoại suy, mức tin cậy, giả định, danh mục kiểm tra, căn cứ chính sách.
  * RAG theo từng phiếu (truy vấn sinh từ reason codes, BM25 + tag).
  * LLM (nếu có OPENAI_API_KEY trong môi trường hoặc tệp .env) chỉ viết lại phần diễn giải và phải qua
    kiểm tra bám bằng chứng (grounding check); nếu không đạt → dùng bản quy tắc.
Biến môi trường: GENAI_MODEL (mặc định gpt-5-mini), GENAI_MAX_CASES (số phiếu ưu tiên gửi LLM, mặc định 30),
BRIEF_TOP (số phiếu xuất Markdown, mặc định 30).
"""
from src.common import *
import pandas as pd, numpy as np, json, os
from datetime import datetime
from src.genai.rag import search, load_chunks
from src.genai.assistant import explain, load_env
from src.genai import decision as D

load_env(ROOT)
o = od("08_genai_decision_support"); bd = o / "decision_briefs"; bd.mkdir(exist_ok=True)
for f in bd.glob("*.md"):
    try: f.unlink()          # làm mới thư mục phiếu Markdown
    except OSError: pass

sel = json.loads((OUT / "04_model_comparison" / "model_selection.json").read_text(encoding="utf-8"))
winner = sel["winner"]
inv = pd.read_csv(OUT / "07_inventory_decision" / "inventory_recommendations.csv")
sc = pd.read_csv(OUT / "06_promotion_scenarios" / "promotion_scenarios.csv")
prob = pd.read_parquet(OUT / "05_probabilistic_forecast" / "probabilistic_predictions.parquet")


def demand_level_calibration():
    """Bao phủ P10–P90 theo tứ phân vị doanh số thực tế của tập kiểm tra cuối (cùng cách tính với Stage 11)."""
    pt = pd.read_parquet(OUT / "04_model_comparison" / "final_holdout_predictions.parquet")
    d = pt.merge(prob[["date", "store_nbr", "family", "p10", "p90"]], on=["date", "store_nbr", "family"], how="left")
    d["covered"] = (d.sales >= d.p10) & (d.sales <= d.p90); d["interval_width"] = d.p90 - d.p10
    d["demand_level"] = pd.qcut(d.sales.rank(method="first"), 4, labels=["Q1 thấp", "Q2", "Q3", "Q4 cao"])
    return d.groupby("demand_level", observed=True).agg(coverage_P10_P90=("covered", "mean"),
                                                        mean_interval_width=("interval_width", "mean")).reset_index()


dl = demand_level_calibration()

ctx = D.build_context(prob, dl, float(inv.critical_fractile.iloc[0]))
daily_g = {k: g for k, g in prob.groupby(["store_nbr", "family"])}
sc_g = {k: g for k, g in sc.groupby(["store_nbr", "family"])}
model_name = os.getenv("GENAI_MODEL", "gpt-5-mini")
max_llm = int(os.getenv("GENAI_MAX_CASES", "30")); brief_top = int(os.getenv("BRIEF_TOP", "30"))

cases = []
for _, r in inv.iterrows():
    key = (r.store_nbr, r.family)
    ev = D.build_evidence(r, daily_g.get(key, prob.iloc[0:0]), sc_g[key], ctx, HORIZON, winner)
    codes = D.reason_codes(ev)
    rec = D.build_recommendation(ev, codes)
    cases.append({"case_id": f"DEC-S{ev['store_nbr']:02d}-{ev['family'].replace(' ', '_').replace('/', '_').replace(',', '_')}",
                  "priority_score": D.priority(codes), "reason_codes": codes, "evidence": ev, "recommendation": rec})

# hàng đợi ưu tiên: điểm lý do ↓, sau đó quy mô P50 ↓ (tác động kinh doanh lớn trước)
cases.sort(key=lambda c: (-c["priority_score"], -c["evidence"]["p50"]))
modes = {}
KB = {k["policy_id"]: k for k in load_chunks(ROOT / "knowledge_base")}
for i, c in enumerate(cases, 1):
    c["priority_rank"] = i
    q, tags = D.query_for(c["evidence"], c["reason_codes"], c["recommendation"])
    hits = search(q, ROOT / "knowledge_base", k=20, tags=tags)
    req = c["recommendation"]["policy_refs"]            # quy định mà quy tắc đã áp dụng → bắt buộc trích dẫn
    hm = {h["policy_id"]: h for h in hits}
    c["sources"] = ([dict(hm.get(pid, {"policy_id": pid, "source_id": KB[pid]["source_id"], "text": KB[pid]["text"], "score": 0.0, "matched": []}), cited_by_rule=True)
                     for pid in req if pid in KB]
                    + [dict(h, cited_by_rule=False) for h in hits if h["policy_id"] not in req][:1])
    if i <= max_llm:
        c["assistant"] = explain(c["evidence"], c["recommendation"], c["sources"], model_name)
    else:
        from src.genai.assistant import rule_based
        c["assistant"] = rule_based(c["recommendation"], "Ngoài nhóm ưu tiên gửi LLM" if os.getenv("OPENAI_API_KEY") else "Không có OPENAI_API_KEY")
    c["approval_status"] = "PENDING_HUMAN_REVIEW"
    modes[c["assistant"]["mode"]] = modes.get(c["assistant"]["mode"], 0) + 1

with open(o / "decision_cases.jsonl", "w", encoding="utf-8") as f:
    for c in cases: f.write(json.dumps(c, ensure_ascii=False, default=str) + "\n")

rows = []
for c in cases:
    ev, rec = c["evidence"], c["recommendation"]
    rows.append({"priority_rank": c["priority_rank"], "case_id": c["case_id"], "store_nbr": ev["store_nbr"], "family": ev["family"],
                 "risk": ev["risk"], "priority_score": c["priority_score"], "reason_codes": "|".join(x["code"] for x in c["reason_codes"]),
                 "p10": ev["p10"], "p50": ev["p50"], "p90": ev["p90"], "relative_uncertainty_r": ev["relative_uncertainty_r"],
                 "action": rec["action"], "chosen_option": rec["chosen_option"], "recommended_qty": rec["quantity"], "target_stock": rec["target"],
                 "confidence": rec["confidence"], "promotion_stance": rec["promotion"]["stance"],
                 "promo_extrapolation": bool(rec["promotion"].get("extrapolation_warning", False)),
                 "policies": "|".join(s["policy_id"] for s in c["sources"]), "assistant_mode": c["assistant"]["mode"],
                 "approval_status": c["approval_status"]})
q = pd.DataFrame(rows); q.to_csv(o / "decision_queue.csv", index=False)

for c in cases[:brief_top]:
    (bd / f"{c['priority_rank']:03d}_{c['case_id']}.md").write_text(D.to_markdown(c), encoding="utf-8")

status = {"run_at": datetime.now().isoformat(timespec="seconds"), "cases": len(cases), "selected_model": winner,
          "selection_method": "Tất cả chuỗi; xếp hạng theo điểm lý do (LARGE_SERIES=+3, RISK_HIGH=+2, RISK_MEDIUM=+1, RISK_LOW=0, PROMO_EXTRAPOLATION=+1), hòa điểm theo P50 giảm dần",
          "api_key_present": bool(os.getenv("OPENAI_API_KEY")), "genai_model": model_name, "llm_case_limit": max_llm,
          "mode_counts": json.dumps(modes, ensure_ascii=False),
          "grounding_failures": sum(1 for c in cases if not c["assistant"]["grounding"]["passed"]),
          "risk_counts": json.dumps(q.risk.value_counts().to_dict()),
          "action_counts": json.dumps(q.action.value_counts().to_dict(), ensure_ascii=False),
          "briefs_exported": min(brief_top, len(cases)),
          "note": "Mọi con số trong phiếu lấy từ Stage 05–07; LLM (nếu có) chỉ viết lại diễn giải và phải qua kiểm tra bám bằng chứng."}
pd.DataFrame([status]).to_csv(o / "genai_run_status.csv", index=False)
print(json.dumps(status, ensure_ascii=False, indent=2))
print(q.head(10)[["priority_rank", "case_id", "risk", "priority_score", "reason_codes", "action", "recommended_qty", "confidence"]].to_string(index=False))
