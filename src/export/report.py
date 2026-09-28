"""Báo cáo tóm tắt 1 trang cho một phạm vi: HTML (in/lưu PDF từ trình duyệt) và PDF A4 (matplotlib).

Mọi con số tính lại trực tiếp từ outputs/ của pipeline; không có số nào nhập tay.
"""
from __future__ import annotations

import html
import io
from datetime import datetime

import numpy as np
import pandas as pd

from .data import Scope, apply_scope, scope_metrics, series_in_scope

INK, PETROL, TEAL, SEA, MIST, AMBER, CORAL, GREEN, GRAY = ("#0E2A33", "#12505F", "#1B8A8F", "#7FC4C4", "#EEF5F5",
                                                           "#E8A33D", "#D05A4E", "#3C8D5A", "#5B6B70")
RISK_C = {"HIGH": CORAL, "MEDIUM": AMBER, "LOW": GREEN}
SHORT = {"BỔ SUNG THEO P90 · RÀ SOÁT KHOẢNG DỰ BÁO": "Theo P90 + rà soát khoảng", "BỔ SUNG THEO P90": "Bổ sung theo P90",
         "BỔ SUNG THẬN TRỌNG": "Bổ sung thận trọng (q*)"}
ORDER = ["No promotion", "Low", "Current", "Medium", "High"]


def vn(x, d=0):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return f"{float(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")


def vp(x, d=1):
    return "—" if x is None or not np.isfinite(x) else vn(100 * x, d) + "%"


def collect(b: dict, sc: Scope) -> dict:
    keys = series_in_scope(b, sc)
    m = scope_metrics(b, keys)
    p = apply_scope(b["pred"], keys)
    daily = p.groupby("date")[["sales", "point", "p10", "p50", "p90"]].sum().reset_index()
    s = apply_scope(b["scen"], keys)
    sc_sum = s.groupby("scenario").p50.sum().reindex(ORDER)
    cur = sc_sum.get("Current", np.nan)
    promo = [(k, float(v), (float(v) / cur - 1) if cur and cur > 0 else np.nan) for k, v in sc_sum.items()]
    q = apply_scope(b["queue"], keys).sort_values("priority_rank")
    winner = (b.get("selection") or {}).get("winner", "XGBoost")
    return dict(scope=sc, m=m, daily=daily, promo=promo, queue=q, winner=winner,
                pm=b["prob_metrics"].iloc[0], stamp=datetime.now().strftime("%d/%m/%Y %H:%M"),
                actions=q.action.value_counts().to_dict(), extrap=int(q.promo_extrapolation.sum()) if len(q) else 0)


# ------------------------------------------------------------------ SVG helpers
def _svg_fan(daily: pd.DataFrame, w=560, h=210) -> str:
    if daily.empty:
        return ""
    L, R, T, B = 52, 12, 14, 30
    xs = np.linspace(L, w - R, len(daily))
    ymax = float(max(daily.p90.max(), daily.sales.max())) * 1.05
    ymin = float(min(daily.p10.min(), daily.sales.min())) * 0.92
    Y = lambda v: T + (h - T - B) * (1 - (v - ymin) / (ymax - ymin + 1e-9))  # noqa: E731
    band = " ".join(f"{x:.1f},{Y(v):.1f}" for x, v in zip(xs, daily.p90)) + " " + " ".join(
        f"{x:.1f},{Y(v):.1f}" for x, v in zip(xs[::-1], daily.p10[::-1]))
    line = lambda col: " ".join(f"{x:.1f},{Y(v):.1f}" for x, v in zip(xs, daily[col]))  # noqa: E731
    ticks = np.linspace(ymin, ymax, 4)
    g = "".join(f'<line x1="{L}" x2="{w-R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="#E3E9EA"/>'
                f'<text x="{L-6}" y="{Y(t)+4:.1f}" text-anchor="end" font-size="10" fill="{GRAY}">{vn(t)}</text>' for t in ticks)
    lab = "".join(f'<text x="{x:.1f}" y="{h-10}" text-anchor="middle" font-size="9.5" fill="{GRAY}">{d:%d/%m}</text>'
                  for i, (x, d) in enumerate(zip(xs, daily.date)) if i % 3 == 0 or i == len(xs) - 1)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{Y(v):.1f}" r="2.6" fill="{INK}"/>' for x, v in zip(xs, daily.sales))
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Tổng thực tế, P50 và P10–P90 theo ngày">{g}'
            f'<polygon points="{band}" fill="{SEA}" fill-opacity=".35"/>'
            f'<polyline points="{line("p50")}" fill="none" stroke="{TEAL}" stroke-width="2.4"/>'
            f'<polyline points="{line("sales")}" fill="none" stroke="{INK}" stroke-width="1.4" stroke-dasharray="3 3"/>{dots}{lab}</svg>')


def _svg_hbars(items, w=300, h=150, fmt=lambda v: vn(v), colors=None) -> str:
    if not items:
        return ""
    L, R = 92, 58
    bh = (h - 10) / len(items)
    vmax = max(abs(v) for _, v in items) or 1
    out = []
    zero = L if min(v for _, v in items) >= 0 else L + (w - L - R) / 2
    span = (w - L - R) if zero == L else (w - L - R) / 2
    for i, (k, v) in enumerate(items):
        y = 5 + i * bh
        bw = span * abs(v) / vmax
        x = zero if v >= 0 else zero - bw
        c = (colors or {}).get(k, TEAL if v >= 0 else CORAL)
        out.append(f'<text x="{L-6}" y="{y+bh/2+4:.1f}" text-anchor="end" font-size="10.5" fill="{INK}">{html.escape(str(k))}</text>'
                   f'<rect x="{x:.1f}" y="{y+3:.1f}" width="{max(bw,1):.1f}" height="{bh-6:.1f}" rx="3" fill="{c}"/>'
                   f'<text x="{(x+bw+4) if v>=0 else (x-4):.1f}" y="{y+bh/2+4:.1f}" text-anchor="{"start" if v>=0 else "end"}" font-size="10" fill="{GRAY}">{fmt(v)}</text>')
    if zero != L:
        out.append(f'<line x1="{zero}" x2="{zero}" y1="2" y2="{h-4}" stroke="#C9D6D8"/>')
    return f'<svg viewBox="0 0 {w} {h}" width="100%">{"".join(out)}</svg>'


CSS = """
@page{size:A4;margin:11mm}
*{box-sizing:border-box}body{font-family:Calibri,"Segoe UI",Arial,sans-serif;color:#0E2A33;margin:0;background:#E9EEF0}
.page{width:210mm;min-height:297mm;margin:12px auto;background:#fff;padding:12mm 12mm 10mm;box-shadow:0 8px 30px rgba(0,0,0,.08)}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.eb{font-size:10px;letter-spacing:.16em;font-weight:700;color:#1B8A8F;text-transform:uppercase}
h1{font-family:Cambria,Georgia,serif;font-size:22px;margin:3px 0 4px;line-height:1.15}
.sub{color:#5B6B70;font-size:11.5px;line-height:1.45}
.badge{background:#0E2A33;color:#fff;border-radius:12px;padding:8px 12px;font-size:11px;text-align:right;white-space:nowrap}
.badge b{display:block;font-size:15px;color:#E8A33D}
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:7px;margin:12px 0}
.k{background:#EEF5F5;border-radius:10px;padding:8px 9px}.k .l{font-size:9.5px;color:#5B6B70;text-transform:uppercase;letter-spacing:.05em;font-weight:700}
.k .v{font-family:Cambria,Georgia,serif;font-size:17px;font-weight:700;color:#12505F;margin-top:2px}.k .n{font-size:9.5px;color:#5B6B70}
.grid{display:grid;grid-template-columns:1.65fr 1fr;gap:10px}
.box{border:1px solid #DDE6E8;border-radius:12px;padding:9px 11px}
.box h3{margin:0 0 4px;font-size:12.5px;color:#12505F}.box .cap{font-size:9.5px;color:#5B6B70;margin-top:2px}
.lg{font-size:9.5px;color:#5B6B70}.lg i{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 3px -1px 8px}
table{width:100%;border-collapse:collapse;font-size:10.3px}th{background:#12505F;color:#fff;text-align:left;padding:5px 6px;font-weight:700}
td{padding:4px 6px;border-bottom:1px solid #E6EDEE}tr:nth-child(even) td{background:#F6FAFA}td.n{text-align:right;font-variant-numeric:tabular-nums}
.r{display:inline-block;border-radius:99px;padding:1px 7px;font-size:9px;font-weight:700;color:#fff}
.notes{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}
.notes ul{margin:4px 0 0 16px;padding:0;font-size:10.2px;line-height:1.45}
.foot{display:flex;justify-content:space-between;color:#8A9A9E;font-size:9px;margin-top:10px;border-top:1px solid #E6EDEE;padding-top:5px}
.print{position:fixed;right:18px;bottom:18px;background:#1B8A8F;color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:700;cursor:pointer;font-size:13px;box-shadow:0 6px 18px rgba(0,0,0,.2)}
@media print{body{background:#fff}.page{margin:0;box-shadow:none;width:auto;min-height:auto;padding:0}.print{display:none}}
"""


def build_html(b: dict, sc: Scope | None = None) -> str:
    d = collect(b, sc or Scope())
    m, pm, q = d["m"], d["pm"], d["queue"]
    rc = m["risk_counts"]
    kp = [("Chuỗi", vn(m["series"]), f"HIGH {rc['HIGH']} · MED {rc['MEDIUM']} · LOW {rc['LOW']}"),
          ("Thực tế 16 ngày", vn(m["actual_sum"]), "tổng đơn vị"), ("Dự báo điểm", vn(m["point_sum"]), f"P50: {vn(m['p50_sum'])}"),
          ("WAPE", vp(m["WAPE"], 2), f"toàn hệ thống {vp(b['holdout'].set_index('model').loc[d['winner']].WAPE, 2)}"),
          ("Bao phủ P10–P90", vp(m["coverage"], 1), "danh nghĩa 80%"), ("Bổ sung gợi ý", vn(m["replenishment_sum"]), "mô phỏng Stage 07")]
    kpis = "".join(f'<div class="k"><div class="l">{a}</div><div class="v">{v}</div><div class="n">{n}</div></div>' for a, v, n in kp)
    promo_items = [(k, r) for k, _, r in d["promo"] if k != "Current" and np.isfinite(r)]
    risk_items = [(k, rc[k]) for k in ("HIGH", "MEDIUM", "LOW")]
    rows = ""
    for r in q.head(10).itertuples():
        rows += (f'<tr><td class="n">{r.priority_rank}</td><td>CH {r.store_nbr} · {html.escape(r.family)}</td>'
                 f'<td><span class="r" style="background:{RISK_C.get(r.risk, GRAY)}">{r.risk}</span></td><td class="n">{vn(r.p50)}</td>'
                 f'<td>{html.escape(r.action)}</td><td class="n"><b>{vn(r.recommended_qty)}</b> ({r.chosen_option})</td><td>{r.confidence}</td>'
                 f'<td>{html.escape(r.promotion_stance)}</td></tr>')
    acts = " · ".join(f"{html.escape(k)}: {vn(v)}" for k, v in d["actions"].items())
    return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>Báo cáo dự báo 1 trang</title><style>{CSS}</style></head><body>
<button class="print" onclick="window.print()">In / Lưu PDF</button>
<div class="page">
<div class="top"><div><div class="eb">Favorita · Forecast Intelligence · báo cáo 1 trang</div>
<h1>Dự báo 16 ngày và khuyến nghị bổ sung hàng</h1>
<div class="sub">{html.escape(d['scope'].label())}<br>Kỳ {m['period'][0]} → {m['period'][1]} (tập kiểm tra cuối) · xuất lúc {d['stamp']}</div></div>
<div class="badge">Mô hình được chọn<b>{d['winner']}</b>WAPE CV {vp(b['cv_summary'].set_index('model').loc[d['winner']].WAPE_mean, 3)}</div></div>
<div class="kpis">{kpis}</div>
<div class="grid">
<div class="box"><h3>Tổng thực tế, P50 và khoảng P10–P90 theo ngày</h3>
<div class="lg"><i style="background:{INK}"></i>Thực tế <i style="background:{TEAL}"></i>P50 <i style="background:{SEA}"></i>Tổng P10–P90</div>
{_svg_fan(d['daily'])}<div class="cap">Tổng các phân vị theo ngày – mang tính mô tả, không phải phân vị chính xác của tổng.</div></div>
<div class="box"><h3>Nhãn rủi ro tồn kho</h3>{_svg_hbars(risk_items, h=92, colors=RISK_C)}
<h3 style="margin-top:6px">Kịch bản khuyến mãi (P50 so với hiện tại)</h3>{_svg_hbars(promo_items, h=118, fmt=lambda v: ("+" if v > 0 else "") + vp(v, 2))}
<div class="cap">Dự báo có điều kiện, không phải tác động nhân quả. Cờ ngoại suy: {d['extrap']} phiếu.</div></div></div>
<div class="box" style="margin-top:10px"><h3>10 phiếu ưu tiên cao nhất trong phạm vi</h3>
<table><tr><th>#</th><th>Chuỗi</th><th>Nhãn</th><th>P50 kỳ</th><th>Hành động</th><th>SL đề xuất (PA)</th><th>Tin cậy</th><th>Khuyến mãi</th></tr>{rows}</table>
<div class="cap">Hành động: {acts}. Mọi phiếu ở trạng thái chờ con người phê duyệt (POL-HITL-001).</div></div>
<div class="notes"><div class="box"><h3>Cách đọc</h3><ul>
<li>P50 là trung vị; P10–P90 là khoảng dự báo 80% danh nghĩa theo nhóm quy mô (Mondrian).</li>
<li>Phương án A = P50, B = q* = 0,75, C = P90; lượng bổ sung = mục tiêu − vị thế giả định (0,8 × P50).</li>
<li>Toàn hệ thống: Pinball P10/P50/P90 = {vn(pm.Pinball_P10, 3)} / {vn(pm.Pinball_P50, 3)} / {vn(pm.Pinball_P90, 3)}; bao phủ {vp(pm.Coverage_P10_P90, 2)}.</li></ul></div>
<div class="box"><h3>Giới hạn cần lưu ý</h3><ul>
<li>Bao phủ tổng thấp hơn danh nghĩa 80%; nhãn rủi ro còn gắn với quy mô chuỗi.</li>
<li>Không có giá, biên lợi nhuận, tồn kho thực, thời gian cung ứng: tồn kho là mô phỏng (Cu = 3, Co = 1).</li>
<li>Đối chiếu tồn kho thực tế trước khi duyệt – dùng Mẫu ra quyết định dự báo (.xlsx).</li></ul></div></div>
<div class="foot"><span>Nguồn: outputs/05, 06, 07, 08 của pipeline · không có số liệu nhập tay</span><span>Đinh Nguyễn Tấn Nguyên · Luận văn Favorita</span></div>
</div></body></html>"""


def build_pdf(b: dict, sc: Scope | None = None) -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.patches import FancyBboxPatch

    d = collect(b, sc or Scope())
    m, pm, q = d["m"], d["pm"], d["queue"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5})
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(.06, .965, "FAVORITA · FORECAST INTELLIGENCE · BÁO CÁO 1 TRANG", color=TEAL, fontsize=7, weight="bold")
    fig.text(.06, .94, "Dự báo 16 ngày và khuyến nghị bổ sung hàng", color=INK, fontsize=15, weight="bold")
    fig.text(.06, .918, d["scope"].label(), color=GRAY, fontsize=7.5)
    fig.text(.06, .904, f"Kỳ {m['period'][0]} → {m['period'][1]} (tập kiểm tra cuối) · mô hình {d['winner']} · xuất lúc {d['stamp']}", color=GRAY, fontsize=7.5)
    rc = m["risk_counts"]
    kp = [("Chuỗi", vn(m["series"]), f"H {rc['HIGH']} · M {rc['MEDIUM']} · L {rc['LOW']}"), ("Thực tế 16 ngày", vn(m["actual_sum"]), "tổng đơn vị"),
          ("Dự báo điểm", vn(m["point_sum"]), f"P50 {vn(m['p50_sum'])}"), ("WAPE", vp(m["WAPE"], 2), "dự báo điểm"),
          ("Bao phủ P10–P90", vp(m["coverage"], 1), "danh nghĩa 80%"), ("Bổ sung gợi ý", vn(m["replenishment_sum"]), "mô phỏng")]
    for i, (a, v, n) in enumerate(kp):
        x = .06 + i * .1497
        fig.patches.append(FancyBboxPatch((x, .835), .14, .055, boxstyle="round,pad=0,rounding_size=.008", transform=fig.transFigure, fc=MIST, ec="none"))
        fig.text(x + .008, .876, a.upper(), fontsize=5.8, color=GRAY, weight="bold")
        fig.text(x + .008, .855, v, fontsize=10.5, color=PETROL, weight="bold")
        fig.text(x + .008, .841, n, fontsize=5.8, color=GRAY)
    ax = fig.add_axes([.09, .63, .54, .17])
    dd = d["daily"]
    ax.fill_between(dd.date, dd.p10, dd.p90, color=SEA, alpha=.4, lw=0, label="Tổng P10–P90")
    ax.plot(dd.date, dd.p50, color=TEAL, lw=2, label="P50")
    ax.plot(dd.date, dd.sales, color=INK, lw=1, ls="--", marker="o", ms=2.5, label="Thực tế")
    ax.set_title("Tổng thực tế, P50 và khoảng P10–P90 theo ngày", loc="left", fontsize=8.5, color=PETROL, weight="bold")
    ax.legend(frameon=False, fontsize=6.5, ncol=3, loc="upper left")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: vn(v)))
    ax.xaxis.set_major_locator(matplotlib.dates.DayLocator(interval=3)); ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d/%m"))
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.grid(axis="y", color="#E3E9EA"); ax.tick_params(labelsize=6.5)
    ax2 = fig.add_axes([.72, .725, .22, .075])
    ks = ["HIGH", "MEDIUM", "LOW"]
    ax2.barh(ks, [rc[k] for k in ks], color=[RISK_C[k] for k in ks]); ax2.invert_yaxis()
    for i, k in enumerate(ks):
        ax2.text(rc[k], i, " " + vn(rc[k]), va="center", fontsize=6.5, color=GRAY)
    ax2.set_title("Nhãn rủi ro tồn kho", loc="left", fontsize=8, color=PETROL, weight="bold")
    ax2.axis("off"); [ax2.text(-.02, i, k, ha="right", va="center", fontsize=6.5, transform=ax2.get_yaxis_transform()) for i, k in enumerate(ks)]
    ax3 = fig.add_axes([.72, .63, .22, .065])
    pi = [(k, r) for k, _, r in d["promo"] if k != "Current" and np.isfinite(r)]
    ax3.barh([k for k, _ in pi], [100 * r for _, r in pi], color=[TEAL if r >= 0 else CORAL for _, r in pi]); ax3.invert_yaxis()
    ax3.axvline(0, color="#C9D6D8", lw=.8); ax3.tick_params(labelsize=6); ax3.set_title("Khuyến mãi: P50 so với hiện tại (%)", loc="left", fontsize=8, color=PETROL, weight="bold")
    for s_ in ("top", "right"):
        ax3.spines[s_].set_visible(False)
    fig.text(.06, .585, "10 phiếu ưu tiên cao nhất trong phạm vi", fontsize=9, color=PETROL, weight="bold")
    axt = fig.add_axes([.06, .375, .88, .2]); axt.axis("off")
    cols = ["#", "Chuỗi", "Nhãn", "P50 kỳ", "Hành động", "SL (PA)", "Tin cậy"]
    cells = [[str(r.priority_rank), f"CH {r.store_nbr} · {r.family}"[:30], r.risk, vn(r.p50), SHORT.get(r.action, r.action)[:34], f"{vn(r.recommended_qty)} ({r.chosen_option})", r.confidence]
             for r in q.head(10).itertuples()]
    if cells:
        t = axt.table(cellText=cells, colLabels=cols, loc="upper left", cellLoc="left", colWidths=[.05, .25, .08, .1, .3, .12, .1])
        t.auto_set_font_size(False); t.set_fontsize(6.5); t.scale(1, 1.35)
        for (i, j), c in t.get_celld().items():
            c.set_edgecolor("#E6EDEE")
            if i == 0:
                c.set_facecolor(PETROL); c.get_text().set_color("white"); c.get_text().set_weight("bold")
            elif j == 2:
                c.get_text().set_color(RISK_C.get(cells[i - 1][2], GRAY)); c.get_text().set_weight("bold")
    notes = [("Cách đọc", ["P50 là trung vị; P10–P90 là khoảng 80% danh nghĩa theo nhóm quy mô (Mondrian).",
                           "Phương án A = P50, B = q* = 0,75, C = P90; bổ sung = mục tiêu − vị thế giả định (0,8 × P50).",
                           f"Toàn hệ thống: Pinball P10/P50/P90 = {vn(pm.Pinball_P10, 3)} / {vn(pm.Pinball_P50, 3)} / {vn(pm.Pinball_P90, 3)}; bao phủ {vp(pm.Coverage_P10_P90, 2)}."]),
             ("Giới hạn", ["Bao phủ tổng thấp hơn 80%; nhãn rủi ro còn gắn với quy mô chuỗi.",
                           "Không có giá, biên lợi nhuận, tồn kho thực, lead time: tồn kho là mô phỏng.",
                           "Kịch bản khuyến mãi là dự báo có điều kiện, không phải nhân quả."])]
    import textwrap
    for i, (h, items) in enumerate(notes):
        x = .06 + i * .45
        fig.text(x, .35, h, fontsize=8.5, color=PETROL, weight="bold")
        y = .333
        for it in items:
            for k, ln in enumerate(textwrap.wrap(it, 64)):
                fig.text(x, y, ("• " if k == 0 else "   ") + ln, fontsize=6.4, color=INK); y -= .0125
            y -= .003
    # mục tiêu theo phương án cho 10 phiếu đầu
    top = q.head(10)
    if len(top):
        axb = fig.add_axes([.09, .06, .85, .14])
        xs = np.arange(len(top)); w_ = .26
        tA, tC = top.p50.to_numpy(), top.p90.to_numpy(); tB = tA + (tC - tA) * (0.75 - 0.5) / (0.9 - 0.5)
        for k, (arr, c, lab) in enumerate([(tA, SEA, "A · P50"), (tB, TEAL, "B · q* = 0,75 (nội suy)"), (tC, PETROL, "C · P90")]):
            axb.bar(xs + (k - 1) * w_, arr, w_, color=c, label=lab)
        axb.scatter(xs, 0.8 * tA, marker="_", s=260, color=CORAL, lw=2, label="Vị thế giả định 0,8 × P50", zorder=3)
        axb.set_xticks(xs, [f"#{r.priority_rank}\nCH {r.store_nbr}\n{r.family[:12]}" for r in top.itertuples()], fontsize=5.8)
        axb.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: vn(v))); axb.tick_params(axis="y", labelsize=6)
        axb.legend(frameon=False, fontsize=6, ncol=4, loc="lower right", bbox_to_anchor=(1, 1.0))
        for s_ in ("top", "right"):
            axb.spines[s_].set_visible(False)
        axb.grid(axis="y", color="#E3E9EA")
        fig.text(.06, .232, "Mức mục tiêu theo ba phương án của 10 phiếu đầu (đơn vị, tổng 16 ngày)", fontsize=8.5, color=PETROL, weight="bold")
    fig.text(.06, .018, "Nguồn: outputs/05, 06, 07, 08 của pipeline · không có số liệu nhập tay", fontsize=6, color=GRAY)
    fig.text(.94, .018, "Đinh Nguyễn Tấn Nguyên · Luận văn Favorita", fontsize=6, color=GRAY, ha="right")
    bio = io.BytesIO()
    with PdfPages(bio) as pdf:
        pdf.savefig(fig)
    plt.close(fig)
    return bio.getvalue()
