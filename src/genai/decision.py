"""Bộ máy khuyến nghị có căn cứ (deterministic decision engine) cho Stage 08.

Mọi con số trong phiếu khuyến nghị đều lấy trực tiếp hoặc tính minh bạch từ đầu ra
của Stage 05 (P10/P50/P90 theo ngày), Stage 06 (kịch bản khuyến mãi) và Stage 07
(đại lượng tồn kho). Mô hình ngôn ngữ (nếu có) chỉ được viết lại phần diễn giải.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

RISK_ORDER = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}          # thứ bậc đúng (sửa lỗi sắp xếp chuỗi ký tự)
RISK_POINTS = {"HIGH": 2, "MEDIUM": 1, "LOW": 0}          # điểm ưu tiên theo bất định tương đối
LARGE_POINTS = 3                                          # chuỗi lớn: tác động kinh doanh + nguy cơ khoảng quá hẹp
DOW_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ nhật"]
EXTRAP_THRESHOLD = 1.0      # |ΔP50| > 100% so với Current → ngoại suy (POL-PROMO-004)
MEANINGFUL_PROMO = 0.02     # thay đổi < 2% coi là không đáng kể


def vn(x, d=0) -> str:
    """Định dạng số kiểu Việt Nam."""
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    s = f"{float(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.replace("-", "−")


def pct(x, d=1) -> str:
    return ("+" if x > 0 else "") + vn(100 * x, d) + "%"


# ----------------------------------------------------------------------------- context
def build_context(prob: pd.DataFrame, demand_level: pd.DataFrame | None, q_star: float) -> dict:
    """Thông tin cấp hệ thống dùng chung cho mọi phiếu."""
    cut = float(prob.p50.quantile(.75))
    ctx = {"q_star": float(q_star), "large_series_daily_p50_cutoff": cut}
    if demand_level is not None and len(demand_level):
        dl = demand_level.set_index("demand_level")
        top = dl.iloc[-1]
        ctx["calibration_top_quartile"] = {"level": str(dl.index[-1]), "coverage": float(top.coverage_P10_P90),
                                           "mean_width": float(top.mean_interval_width)}
        ctx["calibration_bottom_quartile"] = {"level": str(dl.index[0]), "coverage": float(dl.iloc[0].coverage_P10_P90)}
    return ctx


# ----------------------------------------------------------------------------- evidence
def build_evidence(inv_row: pd.Series, daily: pd.DataFrame, scen: pd.DataFrame, ctx: dict, horizon: int, model: str) -> dict:
    daily = daily.sort_values("date")
    p10, p50, p90 = float(inv_row.p10), float(inv_row.p50), float(inv_row.p90)
    r = (p90 - p10) / (p50 + 1)
    order = ["No promotion", "Current", "Low", "Medium", "High"]
    sc = scen.set_index("scenario").reindex(order).dropna(how="all").reset_index()
    cur = float(sc.loc[sc.scenario == "Current", "p50"].iloc[0]) if (sc.scenario == "Current").any() else p50
    srows = []
    for _, s in sc.iterrows():
        rel = float(s.conditional_change_vs_current) / cur if cur > 0 else (np.inf if s.conditional_change_vs_current > 0 else 0.0)
        srows.append({"scenario": s.scenario, "p10": float(s.p10), "p50": float(s.p50), "p90": float(s.p90),
                      "change_vs_current": float(s.conditional_change_vs_current), "rel_change_vs_current": rel})
    peak = daily.loc[daily.p50.idxmax()] if len(daily) else None
    mean_daily = float(daily.p50.mean()) if len(daily) else p50 / horizon
    return {
        "store_nbr": int(inv_row.store_nbr), "family": str(inv_row.family), "horizon_days": horizon,
        "selected_model": model,
        "period": {"start": str(pd.Timestamp(daily.date.min()).date()) if len(daily) else None,
                   "end": str(pd.Timestamp(daily.date.max()).date()) if len(daily) else None},
        "p10": p10, "p50": p50, "p90": p90, "relative_uncertainty_r": r, "risk": str(inv_row.risk),
        "critical_fractile": float(inv_row.critical_fractile),
        "assumed_inventory_position": float(inv_row.assumed_inventory_position),
        "reorder_point_proxy": float(inv_row.reorder_point_proxy),
        "safety_stock_proxy": float(inv_row.safety_stock_proxy),
        "suggested_replenishment_scenario": float(inv_row.suggested_replenishment),
        "mean_daily_p50": mean_daily,
        "current_onpromotion_mean": float(daily.onpromotion.mean()) if "onpromotion" in daily and len(daily) else None,
        "peak_day": ({"date": str(pd.Timestamp(peak.date).date()), "dow": DOW_VI[pd.Timestamp(peak.date).dayofweek],
                      "p50": float(peak.p50)} if peak is not None else None),
        "daily": [{"date": str(pd.Timestamp(d.date).date()), "p10": float(d.p10), "p50": float(d.p50), "p90": float(d.p90)}
                  for _, d in daily.iterrows()],
        "promotion_scenarios": srows,
        "system_context": ctx,
    }


# ----------------------------------------------------------------------------- rules
def reason_codes(ev: dict) -> list[dict]:
    ctx = ev["system_context"]
    codes = []
    tier = ev["risk"]
    codes.append({"code": f"RISK_{tier}", "points": RISK_POINTS.get(tier, 0),
                  "text": f"Nhãn bất định tương đối {tier} (r = (P90 − P10)/(P50 + 1) = {vn(ev['relative_uncertainty_r'], 3)}).",
                  "tags": (["uncertainty", "high_risk", "small_series", "overstock"] if tier == "HIGH" else (["uncertainty"] if tier == "MEDIUM" else []))})
    if ev["mean_daily_p50"] >= ctx["large_series_daily_p50_cutoff"]:
        cal = ctx.get("calibration_top_quartile", {})
        extra = (f" Trên tập kiểm tra của lần chạy, độ bao phủ P10–P90 ở nhóm quan sát nhu cầu cao nhất chỉ {vn(100*cal['coverage'],1)}%."
                 if cal else "")
        codes.append({"code": "LARGE_SERIES", "points": LARGE_POINTS,
                      "text": f"Chuỗi quy mô lớn (P50 trung bình {vn(ev['mean_daily_p50'],1)}/ngày ≥ {vn(ctx['large_series_daily_p50_cutoff'],1)}, là phân vị 75% của P50 theo ngày trên toàn bộ 1.782 chuỗi): khoảng dự báo có thể quá hẹp so với quy mô.{extra}",
                      "tags": ["large_series", "calibration", "coverage", "review"]})
    ext = [s for s in ev["promotion_scenarios"] if s["scenario"] != "Current" and abs(s["rel_change_vs_current"]) > EXTRAP_THRESHOLD]
    if ext:
        worst = max(ext, key=lambda s: abs(s["rel_change_vs_current"]))
        rel = worst["rel_change_vs_current"]
        codes.append({"code": "PROMO_EXTRAPOLATION", "points": 1,
                      "text": f"Kịch bản {worst['scenario']} làm P50 thay đổi {pct(rel,0) if np.isfinite(rel) else 'rất lớn (P50 hiện tại ≈ 0)'} so với hiện tại → ngoại suy ngoài miền dữ liệu.",
                      "tags": ["promotion", "extrapolation", "out_of_domain"]})
    return codes


ACTION_PHRASE = {"BỔ SUNG THẬN TRỌNG": "bổ sung thận trọng theo phân vị tới hạn q*",
                 "BỔ SUNG THEO P90": "bổ sung theo mức P90",
                 "BỔ SUNG THEO P90 · RÀ SOÁT KHOẢNG DỰ BÁO": "bổ sung theo mức P90 và rà soát lại khoảng dự báo"}


def build_recommendation(ev: dict, codes: list[dict]) -> dict:
    p10, p50, p90 = ev["p10"], ev["p50"], ev["p90"]
    pos = ev["assumed_inventory_position"]
    q = ev["critical_fractile"]
    flags = {c["code"] for c in codes}
    # P_q xấp xỉ bằng nội suy tuyến tính giữa P50 (0,5) và P90 (0,9)
    pq = p50 + (p90 - p50) * (q - .5) / .4 if .5 <= q <= .9 else (p90 if q > .9 else p50)
    options = [
        {"key": "A", "name": "Theo P50 (trung vị)", "target": p50, "qty": max(p50 - pos, 0.0),
         "tradeoff": "Tồn dư thấp nhất; xác suất thiếu hàng khoảng 50% theo mô hình."},
        {"key": "B", "name": f"Theo q* = {vn(q,2)} (xấp xỉ P{int(round(q*100))})", "target": pq, "qty": max(pq - pos, 0.0),
         "tradeoff": "Cân bằng theo tỷ lệ chi phí Cu/Co; giá trị phân vị là xấp xỉ nội suy giữa P50 và P90."},
        {"key": "C", "name": "Theo P90 (bảo thủ)", "target": p90, "qty": max(p90 - pos, 0.0),
         "tradeoff": "Giảm nguy cơ thiếu hàng; chấp nhận tồn dư cao hơn."},
    ]
    if "RISK_HIGH" in flags and "LARGE_SERIES" not in flags:
        chosen, action, basis = "B", "BỔ SUNG THẬN TRỌNG", "POL-INV-005"
    else:
        chosen, action, basis = "C", "BỔ SUNG THEO P90", "POL-INV-002"
    if "LARGE_SERIES" in flags:
        action = "BỔ SUNG THEO P90 · RÀ SOÁT KHOẢNG DỰ BÁO"
    opt = next(o for o in options if o["key"] == chosen)
    conf = 3 - ("RISK_HIGH" in flags) - ("LARGE_SERIES" in flags)
    confidence = {3: "CAO", 2: "TRUNG BÌNH"}.get(conf, "THẤP")
    conf_reason = []
    if "RISK_HIGH" in flags: conf_reason.append("bất định tương đối cao so với quy mô")
    if "LARGE_SERIES" in flags: conf_reason.append("khoảng dự báo có thể bị đánh giá hẹp ở chuỗi lớn")
    if not conf_reason: conf_reason.append("bất định tương đối thấp và không thuộc nhóm có vấn đề hiệu chỉnh")

    # khuyến mãi
    sc = [s for s in ev["promotion_scenarios"] if s["scenario"] != "Current"]
    ext = "PROMO_EXTRAPOLATION" in flags
    up = [s for s in sc if abs(s["rel_change_vs_current"]) <= EXTRAP_THRESHOLD and s["rel_change_vs_current"] > MEANINGFUL_PROMO]
    if up:
        b = max(up, key=lambda s: s["rel_change_vs_current"])
        promo = {"stance": "CÂN NHẮC THỬ NGHIỆM", "scenario": b["scenario"], "rel_change": b["rel_change_vs_current"],
                 "text": f"Kịch bản {b['scenario']} cho P50 {vn(b['p50'])} ({pct(b['rel_change_vs_current'])} so với hiện tại). Đây là dự báo có điều kiện, không phải tác động nhân quả: chỉ nên thử nghiệm có đối chứng và không phê duyệt tự động khi thiếu dữ liệu biên lợi nhuận/ngân sách."}
    else:
        promo = {"stance": "KHÔNG ĐỀ XUẤT TĂNG", "scenario": None, "rel_change": 0.0,
                 "text": "Không có kịch bản khuyến mãi nào trong miền tin cậy làm P50 tăng đáng kể (> 2%); chưa có cơ sở đề xuất tăng khuyến mãi."}
    if ext:
        promo["text"] += " Lưu ý: có kịch bản làm P50 thay đổi hơn 100% so với hiện tại — coi là ngoại suy, không dùng để lập kế hoạch."
        promo["extrapolation_warning"] = True

    peak = ev.get("peak_day")
    summary = (f"Nhu cầu {ev['horizon_days']} ngày của cửa hàng {ev['store_nbr']} – {ev['family']} có trung vị (P50) {vn(p50)} đơn vị, "
               f"khoảng P10–P90 từ {vn(p10)} đến {vn(p90)}. Khuyến nghị: {ACTION_PHRASE[action]}, bổ sung {vn(opt['qty'])} đơn vị để đạt mức mục tiêu "
               f"{vn(opt['target'])} (phương án {chosen}), với vị thế tồn kho giả định {vn(pos)}. Mức tin cậy: {confidence.lower()}.")
    rationale = [c["text"] for c in codes]
    rationale.append(f"Phân vị tới hạn q* = Cu/(Cu + Co) = {vn(q,2)}; mức mục tiêu tham chiếu theo quy định {basis}.")
    if peak:
        rationale.append(f"Ngày có P50 cao nhất trong kỳ: {peak['dow']} {pd.Timestamp(peak['date']).strftime('%d/%m/%Y')} ({vn(peak['p50'],1)} đơn vị) — ưu tiên bảo đảm hàng trước ngày này.")
    checklist = [
        "Đối chiếu vị thế tồn kho thực tế (hiện đang dùng giả định 0,8 × P50) và hàng đang về.",
        "Xác nhận thời gian cung ứng và lịch giao hàng của nhà cung cấp.",
        "Kiểm tra sức chứa kho và hạn sử dụng (đặc biệt với hàng tươi sống).",
        "Chọn phương án số lượng A/B/C hoặc nhập số lượng khác, ghi rõ lý do.",
    ]
    if "LARGE_SERIES" in flags: checklist.insert(1, "Rà soát lại khoảng dự báo: với chuỗi lớn, khoảng P10–P90 có thể hẹp hơn biến động thực tế.")
    if promo["stance"] == "CÂN NHẮC THỬ NGHIỆM": checklist.append("Nếu muốn thử khuyến mãi: bổ sung dữ liệu biên lợi nhuận/ngân sách và thiết kế nhóm đối chứng.")
    assumptions = [
        f"Vị thế tồn kho = 0,8 × P50 = {vn(pos)} (giả định của Stage 07, không phải tồn kho thực).",
        "Chi phí thiếu hàng Cu = 3, chi phí tồn dư Co = 1 (giả định kịch bản).",
        f"P10/P50/P90 của kỳ là tổng của {ev['horizon_days']} phân vị theo ngày — mang tính mô tả, không phải phân vị chính xác của tổng nhu cầu.",
        "Không có dữ liệu giá bán, biên lợi nhuận và thời gian cung ứng.",
    ]
    refs = [basis, "POL-INV-003", "POL-INV-001"]
    if "LARGE_SERIES" in flags: refs.insert(0, "POL-INV-004")
    if ext: refs.append("POL-PROMO-004")
    if promo["stance"] == "CÂN NHẮC THỬ NGHIỆM": refs += ["POL-PROMO-005", "POL-PROMO-003"]
    refs += ["POL-PROMO-002", "POL-HITL-001"]
    return {"policy_refs": list(dict.fromkeys(refs)), "action": action, "chosen_option": chosen, "options": options, "quantity": opt["qty"], "target": opt["target"],
            "confidence": confidence, "confidence_reason": "; ".join(conf_reason), "executive_summary": summary,
            "rationale": rationale, "promotion": promo, "checklist": checklist, "assumptions": assumptions}


def query_for(ev: dict, codes: list[dict], rec: dict | None = None) -> tuple[str, list[str]]:
    tags = ["inventory", "replenishment", "options", "approval", "audit"]
    for c in codes: tags += c["tags"]
    if rec and rec["promotion"]["stance"] == "CÂN NHẮC THỬ NGHIỆM": tags += ["margin", "budget", "experiment", "causal"]
    q = "inventory replenishment newsvendor p90 options human review approval audit promotion scenario " + " ".join(c["code"].lower() for c in codes)
    return q, sorted(set(tags))


def priority(codes: list[dict]) -> int:
    return int(sum(c["points"] for c in codes))


def to_markdown(case: dict) -> str:
    ev, rec, a = case["evidence"], case["recommendation"], case["assistant"]
    L = [f"# PHIẾU KHUYẾN NGHỊ {case['case_id']}", "",
         f"**Cửa hàng {ev['store_nbr']} – {ev['family']}** · Kỳ {ev['horizon_days']} ngày ({ev['period']['start']} → {ev['period']['end']}) · Mô hình: {ev['selected_model']}",
         f"**Ưu tiên:** #{case['priority_rank']} (điểm {case['priority_score']}) · **Nhãn:** {ev['risk']} · **Tin cậy:** {rec['confidence']} · **Trạng thái:** {case['approval_status']}", "",
         "## 1. Tóm tắt điều hành", a.get("executive_summary", rec["executive_summary"]), "",
         f"## 2. Khuyến nghị tồn kho — {rec['action']}", "",
         "| Phương án | Mức mục tiêu | Số lượng bổ sung | Đánh đổi |", "|---|---:|---:|---|"]
    for o in rec["options"]:
        mark = " ✅" if o["key"] == rec["chosen_option"] else ""
        L.append(f"| {o['key']}. {o['name']}{mark} | {vn(o['target'])} | {vn(o['qty'])} | {o['tradeoff']} |")
    L += ["", "## 3. Khuyến mãi — " + rec["promotion"]["stance"], a.get("promotion_note", rec["promotion"]["text"]), "",
          "| Kịch bản | P50 | Chênh lệch so với hiện tại |", "|---|---:|---:|"]
    for s in ev["promotion_scenarios"]:
        rel = s["rel_change_vs_current"]
        L.append(f"| {s['scenario']} | {vn(s['p50'])} | {vn(s['change_vs_current'])} ({pct(rel) if np.isfinite(rel) else '—'}) |")
    L += ["", "## 4. Cơ sở khuyến nghị"] + [f"- {x}" for x in a.get("rationale", rec["rationale"])]
    L += ["", "## 5. Căn cứ chính sách (truy xuất RAG)"] + [f"- **{s['policy_id']}** ({s['source_id']}): {s['text']}" for s in case["sources"]]
    L += ["", "## 6. Giả định"] + [f"- {x}" for x in rec["assumptions"]]
    L += ["", "## 7. Danh mục kiểm tra trước khi phê duyệt"] + [f"- [ ] {x}" for x in rec["checklist"]]
    L += ["", "---", f"*Chế độ tạo diễn giải: {a.get('mode')}. Trợ lý AI không tạo số liệu dự báo; mọi con số lấy từ đầu ra của quy trình. Quyết định cuối cùng thuộc về người phê duyệt.*"]
    return "\n".join(L)
