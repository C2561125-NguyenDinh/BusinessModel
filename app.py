"""Favorita Forecast Intelligence — dashboard trình bày kết quả pipeline (Streamlit).

Dashboard chỉ đọc đầu ra thật của các Stage 01–12 trong thư mục outputs/; không tự tạo số liệu mô hình.
Chạy:  streamlit run app.py
"""
import json
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from src.common import ROOT, OUT

st.set_page_config(page_title="Favorita Forecast Intelligence", page_icon="◈", layout="wide",
                   initial_sidebar_state="expanded")

# =============================================================================== DESIGN SYSTEM
C = dict(navy="#0E2A33", ink="#0E2A33", muted="#5B6B70", line="#DDE6E8", blue="#1B8A8F", sky="#7FC4C4",
         green="#3C8D5A", amber="#E8A33D", red="#D05A4E", violet="#12505F", slate="#9AAEB2", teal="#2FA39A")
RISK_COLOR = {"HIGH": C["red"], "MEDIUM": C["amber"], "LOW": C["green"]}
pio.templates["fav"] = go.layout.Template(layout=go.Layout(
    font=dict(family="Be Vietnam Pro, Segoe UI, Arial", color="#2B3F45", size=13),
    colorway=[C["blue"], C["violet"], C["teal"], C["amber"], C["red"], C["sky"], C["green"], C["slate"]],
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False, linecolor="#EAECF0", ticks="outside", tickcolor="#EAECF0"),
    yaxis=dict(gridcolor="#F2F4F7", zeroline=False),
    hoverlabel=dict(bgcolor="white", bordercolor="#E4E7EC", font=dict(color="#101828")),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=10, r=10, t=56, b=10), title=dict(font=dict(size=15, color="#101828"), x=0, xanchor="left")))
pio.templates.default = "plotly_white+fav"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stMarkdown{font-family:"Be Vietnam Pro",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
.stApp{background:radial-gradient(1200px 520px at 92% -12%,#D6EEEE 0%,rgba(214,238,238,0) 60%),#F4F8F8}
header[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:2.4rem;padding-bottom:3rem;max-width:1520px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0B2229 0%,#0E2A33 55%,#12505F 100%);border-right:1px solid rgba(255,255,255,.06)}
[data-testid="stSidebar"] *{color:#E6EAF2}
[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:10px;padding:7px 10px;margin:1px 0;transition:.15s}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:rgba(255,255,255,.07)}
.brand{font-weight:800;font-size:1.25rem;letter-spacing:.02em}.brand span{color:#E8A33D}
.hero{position:relative;overflow:hidden;background:linear-gradient(115deg,#0E2A33 0%,#12505F 58%,#1B8A8F 125%);
 border-radius:22px;padding:26px 30px;color:#fff;margin-bottom:16px;box-shadow:0 18px 40px rgba(15,23,42,.16)}
.hero:after{content:"";position:absolute;right:-60px;top:-80px;width:320px;height:320px;border-radius:50%;
 background:radial-gradient(circle,rgba(232,163,61,.30),rgba(232,163,61,0) 70%)}
.hero h1{font-size:1.85rem;margin:0 0 6px;font-weight:800;letter-spacing:-.03em;color:#fff}
.hero p{margin:0;color:#CFE8E8;font-size:.98rem}
.eyebrow{font-size:.72rem;text-transform:uppercase;letter-spacing:.14em;font-weight:700;color:#F2C27A;margin-bottom:6px}
.sec{display:flex;align-items:flex-end;justify-content:space-between;margin:22px 0 8px}
.sec-t{font-size:1.15rem;font-weight:750;color:#101828}.sec-s{color:#667085;font-size:.88rem;margin-top:2px}
.card{background:#fff;border:1px solid #E4E7EC;border-radius:16px;padding:16px 18px;box-shadow:0 2px 10px rgba(16,24,40,.04);height:100%}
.card h4{margin:0 0 6px;font-size:.98rem;color:#101828}.card p{color:#667085;margin:0;font-size:.88rem;line-height:1.45}
.kpi{min-height:112px;background:#fff;border:1px solid #E4E7EC;border-radius:16px;padding:14px 16px;box-shadow:0 2px 10px rgba(16,24,40,.04);position:relative;overflow:hidden}
.kpi:before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--tone,#1B8A8F)}
.kpi-l{color:#667085;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em}
.kpi-v{font-size:1.5rem;font-weight:800;color:#101828;margin-top:2px;letter-spacing:-.03em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kpi-n{font-size:.75rem;color:#98A2B3;margin-top:1px}
.pill{display:inline-block;padding:3px 10px;border-radius:999px;font-size:.72rem;font-weight:700;margin:2px 4px 2px 0;border:1px solid transparent}
.p-red{background:#FEF3F2;color:#B42318;border-color:#FECDCA}.p-amber{background:#FFFAEB;color:#B54708;border-color:#FEDF89}
.p-green{background:#ECFDF3;color:#027A48;border-color:#ABEFC6}.p-blue{background:#E3F2F2;color:#12505F;border-color:#B5DCDC}
.p-violet{background:#E8EEF7;color:#2E4A7A;border-color:#C9D5EA}.p-gray{background:#F2F4F7;color:#344054;border-color:#E4E7EC}
.winner{background:linear-gradient(110deg,#ECFDF3,#F6FEF9);border:1px solid #ABEFC6;border-radius:16px;padding:14px 18px;margin:4px 0 12px}
.winner .t{color:#027A48;font-size:.72rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase}
.winner .n{font-size:1.35rem;font-weight:800;color:#05603A;margin:2px 0 4px}
.steps{display:flex;flex-wrap:wrap;gap:8px}.step{background:#fff;border:1px solid #E4E7EC;border-radius:12px;padding:8px 12px;font-size:.82rem;font-weight:600;color:#344054}
.step b{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;background:#E3F2F2;color:#12505F;margin-right:6px;font-size:.72rem}
.insight{border-left:4px solid var(--tone,#1B8A8F)}
.dc{background:linear-gradient(135deg,#0E2A33 0%,#12505F 70%,#1B6F75 100%);color:#fff;border-radius:22px;padding:22px 24px;box-shadow:0 16px 36px rgba(15,23,42,.18)}
.dc .id{font-size:.75rem;color:#F2C27A;font-weight:700;letter-spacing:.12em}
.dc h2{margin:4px 0 6px;font-size:1.45rem;color:#fff;letter-spacing:-.02em}
.dc .act{font-size:1.05rem;font-weight:800;color:#FDE68A;letter-spacing:.02em;margin-top:8px}
.dc .qty{font-size:2.2rem;font-weight:800;color:#fff;letter-spacing:-.03em;line-height:1.1}
.dc .sub{color:#CFE8E8;font-size:.85rem}.dc p{color:#E6F4F4;font-size:.92rem;line-height:1.5;margin:10px 0 0}
.opt{background:#fff;border:1px solid #E4E7EC;border-radius:14px;padding:12px 14px;height:100%}
.opt.sel{border:2px solid #1B8A8F;box-shadow:0 6px 18px rgba(27,138,143,.18)}
.opt .k{font-size:.72rem;font-weight:800;color:#667085;letter-spacing:.08em}.opt .v{font-size:1.35rem;font-weight:800;color:#101828}
.opt .s{font-size:.78rem;color:#667085}
.meter{height:8px;border-radius:99px;background:#E4E7EC;overflow:hidden;margin-top:6px}.meter>div{height:100%;border-radius:99px}
.policy{background:#fff;border:1px solid #E4E7EC;border-radius:12px;padding:10px 12px;margin-bottom:8px}
.policy b{color:#12505F}.policy small{color:#98A2B3}
.reason{background:#F8FAFC;border:1px dashed #D0D5DD;border-radius:12px;padding:8px 12px;margin-bottom:6px;font-size:.86rem;color:#344054}
.foot{color:#98A2B3;font-size:.76rem;margin-top:26px;text-align:center}
div[data-testid="stDataFrame"]{border:1px solid #E4E7EC;border-radius:14px;overflow:hidden;background:#fff}
.stTabs [data-baseweb="tab-list"]{gap:6px;background:#fff;padding:6px;border:1px solid #E4E7EC;border-radius:14px}
.stTabs [data-baseweb="tab"]{border-radius:10px;padding:8px 14px;font-weight:600}
.stTabs [aria-selected="true"]{background:#E3F2F2!important;color:#12505F!important}
.stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{border-radius:11px;font-weight:650;min-height:42px}
div[data-testid="stExpander"]{border:1px solid #E4E7EC;border-radius:13px;background:#fff}
[data-testid="stAlert"]{border-radius:14px}
</style>""", unsafe_allow_html=True)


# =============================================================================== HELPERS
@st.cache_data(show_spinner=False)
def _csv(p, mtime):
    return pd.read_csv(p)


@st.cache_data(show_spinner=False)
def _pq(p, mtime):
    return pd.read_parquet(p)


def csv(rel):
    p = OUT / rel
    return _csv(str(p), p.stat().st_mtime) if p.exists() else None


def pq(rel):
    p = OUT / rel
    return _pq(str(p), p.stat().st_mtime) if p.exists() else None


def jsonf(rel, default=None):
    p = OUT / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else (default or {})


@st.cache_data(show_spinner=False)
def _jsonl(p, mtime):
    return [json.loads(z) for z in open(p, encoding="utf-8") if z.strip()]


def vn(x, d=0):
    if x is None or (isinstance(x, float) and not np.isfinite(x)) or pd.isna(x): return "—"
    return f"{float(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")


def vp(x, d=1): return "—" if x is None or pd.isna(x) else vn(100 * x, d) + "%"


def kpi(label, value, note="", tone=C["blue"]):
    st.markdown(f'<div class="kpi" style="--tone:{tone}"><div class="kpi-l">{label}</div><div class="kpi-v">{value}</div><div class="kpi-n">{note}</div></div>', unsafe_allow_html=True)


def sec(title, sub=""):
    st.markdown(f'<div class="sec"><div><div class="sec-t">{title}</div><div class="sec-s">{sub}</div></div></div>', unsafe_allow_html=True)


def card(title, body, tone=None):
    stl = f' style="--tone:{tone}"' if tone else ""
    cls = "card insight" if tone else "card"
    st.markdown(f'<div class="{cls}"{stl}><h4>{title}</h4><p>{body}</p></div>', unsafe_allow_html=True)


def pill(text, kind="gray"): return f'<span class="pill p-{kind}">{text}</span>'


def risk_pill(r): return pill(r, {"HIGH": "red", "MEDIUM": "amber", "LOW": "green"}.get(r, "gray"))


def chart(fig, h=380):
    fig.update_layout(height=h)
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


def empty():
    card("Chưa có kết quả pipeline", "Chạy <b>START_WINDOWS.bat</b> để tạo đầu ra. Dashboard chỉ hiển thị kết quả thật do pipeline tạo ra.")


def model_colors(models, winner):
    return {m: (C["blue"] if m == winner else "#BFE0E0") for m in models}


def fan(x, title, actual=None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x.date, y=x.p90, line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x.date, y=x.p10, name="Khoảng P10–P90", fill="tonexty", fillcolor="rgba(27,138,143,.18)", line=dict(width=0)))
    fig.add_trace(go.Scatter(x=x.date, y=x.p50, name="P50", line=dict(color=C["blue"], width=3)))
    if actual is not None:
        fig.add_trace(go.Scatter(x=x.date, y=actual, name="Thực tế", mode="lines+markers", line=dict(color=C["ink"], width=1.6, dash="dot"), marker=dict(size=6)))
    fig.update_layout(title=title, hovermode="x unified")
    return fig


# =============================================================================== EXPORT HELPERS
def _out_stamp():
    fs = [OUT / r for r in ("05_probabilistic_forecast/probabilistic_predictions.parquet", "07_inventory_decision/inventory_recommendations.csv",
                            "08_genai_decision_support/decision_queue.csv")]
    return tuple(round(f.stat().st_mtime) if f.exists() else 0 for f in fs)


@st.cache_resource(show_spinner=False)
def _bundle(stamp, with_cases=True):
    from src.export.data import load_bundle
    return load_bundle(OUT, with_cases=with_cases)


def _scope(stores=(), families=(), risks=()):
    from src.export.data import Scope
    return Scope(list(stores), list(families), list(risks))


@st.cache_data(show_spinner=False, max_entries=16)
def export_file(kind, stores, families, risks, stamp):
    from src.export import decision_template, excel_report, report
    b = _bundle(stamp); sc = _scope(stores, families, risks)
    if kind == "xlsx":
        return excel_report.build_workbook(b, sc)
    if kind == "tpl":
        return decision_template.build_template(b, sc, cases=b.get("cases"))
    if kind == "html":
        return report.build_html(b, sc).encode("utf-8")
    if kind == "pdf":
        return report.build_pdf(b, sc)
    raise ValueError(kind)


@st.cache_data(show_spinner="Đang tạo mẫu quyết định…", max_entries=8)
def _tpl_for(case_ids, stamp):
    from src.export import decision_template
    b = _bundle(stamp)
    keys = b["queue"][b["queue"].case_id.isin(case_ids)][["store_nbr", "family"]].drop_duplicates()
    bb = dict(b); bb["inv"] = b["inv"].merge(keys, on=["store_nbr", "family"])
    return decision_template.build_template(bb, _scope(), cases=b.get("cases"))


def export_ready():
    try:
        import openpyxl  # noqa: F401
        return True
    except ImportError:
        st.error("Thiếu thư viện openpyxl để xuất Excel. Chạy: pip install openpyxl (đã thêm vào requirements.txt).")
        return False


sel = jsonf("04_model_comparison/model_selection.json", {"winner": "N/A"})
winner = sel.get("winner", "N/A")

# =============================================================================== SIDEBAR
st.sidebar.markdown('<div class="brand">◈ FAVORITA <span>FI</span></div>', unsafe_allow_html=True)
st.sidebar.caption("FORECAST INTELLIGENCE · 16 NGÀY · 5 MÔ HÌNH")
PAGES = ["Tổng quan điều hành", "01 · Dữ liệu & EDA", "02 · Phân tích chuỗi thời gian", "03 · So sánh mô hình",
         "04 · Dự báo xác suất", "05 · Mô phỏng khuyến mãi", "06 · Tồn kho & Rủi ro", "07 · Trung tâm quyết định AI",
         "08 · Phân tích sai số & Case Study", "09 · Kết quả nghiên cứu", "10 · Xuất báo cáo & Mẫu quyết định"]
page = st.sidebar.radio("KHÔNG GIAN PHÂN TÍCH", PAGES, label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Mô hình được chọn**  \n🏆 **{winner}**")
st.sidebar.caption("Chọn bằng WAPE trung bình của 3 lần kiểm định chéo cuốn chiếu, trước khi mở tập kiểm tra cuối.")
gs = csv("08_genai_decision_support/genai_run_status.csv")
if gs is not None and "mode_counts" in gs:
    st.sidebar.markdown("---")
    live = bool(gs.api_key_present.iloc[0])
    st.sidebar.markdown(f"**Lớp GenAI**  \n{'🟢 LLM đang bật' if live else '🟡 Bộ máy quy tắc (chưa có khóa API)'}")
st.sidebar.markdown("---")
st.sidebar.markdown("**Xuất dữ liệu**  \n📦 Excel · 📄 Báo cáo 1 trang · 📝 Mẫu quyết định")
st.sidebar.caption("Mở trang 10 để chọn phạm vi và tải tệp.")

HERO = {
    "Tổng quan điều hành": ("TỔNG QUAN", "Nền tảng Dự báo & Hỗ trợ Quyết định Favorita", "Từ dữ liệu bán lẻ đến dự báo xác suất, mô phỏng khuyến mãi, rủi ro tồn kho và phiếu khuyến nghị AI có người phê duyệt."),
    "10 · Xuất báo cáo & Mẫu quyết định": ("XUẤT DỮ LIỆU", "Trung tâm xuất báo cáo & mẫu ra quyết định", "Chọn phạm vi, tải workbook Excel nhiều sheet, báo cáo 1 trang (HTML/PDF) và mẫu dự báo để người lập kế hoạch phê duyệt."),
    "07 · Trung tâm quyết định AI": ("TRUNG TÂM QUYẾT ĐỊNH", "Phiếu khuyến nghị có căn cứ · RAG · Human-in-the-loop", "Mọi con số lấy từ pipeline; AI chỉ diễn giải và mọi quyết định đều được con người phê duyệt, ghi nhật ký."),
}
eb, h1, sub = HERO.get(page, ("PHÂN TÍCH", page.split("·")[-1].strip(), "Kết quả đọc trực tiếp từ đầu ra của pipeline."))
st.markdown(f'<div class="hero"><div class="eyebrow">{eb}</div><h1>{h1}</h1><p>{sub}</p></div>', unsafe_allow_html=True)

# =============================================================================== 00 OVERVIEW
if page == "Tổng quan điều hành":
    q = csv("01_data_validation/data_quality.csv"); fm = csv("04_model_comparison/final_holdout_metrics.csv")
    cv = csv("04_model_comparison/model_comparison_summary.csv"); pm = csv("05_probabilistic_forecast/probabilistic_metrics.csv")
    inv = csv("07_inventory_decision/inventory_recommendations.csv"); dl = csv("11_forecast_diagnostics/error_by_demand_level.csv")
    dq = csv("08_genai_decision_support/decision_queue.csv")
    if q is None or fm is None or cv is None: empty()
    else:
        wr = fm[fm.model == winner].iloc[0]; wc = cv[cv.model == winner].iloc[0]
        c = st.columns(6)
        with c[0]: kpi("Số quan sát", vn(q.rows.iloc[0]), f"{vn(q.stores.iloc[0])} cửa hàng · {vn(q.families.iloc[0])} nhóm")
        with c[1]: kpi("Số chuỗi", vn(q.series.iloc[0]), "Store × Family", C["violet"])
        with c[2]: kpi("Mô hình thắng", winner, "chọn trước tập kiểm tra cuối", C["green"])
        with c[3]: kpi("WAPE kiểm định chéo", vp(wc.WAPE_mean, 2), f"±{vp(wc.WAPE_std, 2)} giữa 3 lần", C["teal"])
        with c[4]: kpi("WAPE tập kiểm tra cuối", vp(wr.WAPE, 2), "16 ngày cuối", C["amber"])
        with c[5]: kpi("Bao phủ P10–P90", vp(pm.Coverage_P10_P90.iloc[0]) if pm is not None else "—", "mức danh nghĩa 80%", C["red"])
        sec("Quy trình 14 bước", "Mỗi bước tạo đầu ra riêng trong outputs/ và có thể kiểm tra độc lập.")
        steps = [("01", "Kiểm tra dữ liệu"), ("02", "EDA + Robust STL"), ("03", "Đặc trưng theo ngày lịch"), ("04", "So sánh 5 mô hình"), ("05", "P10/P50/P90 Mondrian"),
                 ("06", "Kịch bản khuyến mãi"), ("07", "Tồn kho & rủi ro"), ("08", "Phiếu khuyến nghị + RAG"), ("09", "Tổng hợp"), ("10", "Kiểm thử"),
                 ("11", "Chẩn đoán sai số"), ("12", "Case study"), ("13", "REPORT_READY"), ("14", "Thí nghiệm độ nhạy")]
        st.markdown('<div class="steps">' + "".join(f'<div class="step"><b>{i}</b>{s}</div>' for i, s in steps) + "</div>", unsafe_allow_html=True)
        l, r = st.columns([1.35, 1])
        with l:
            sec("Bảng xếp hạng mô hình", "WAPE kiểm định chéo (trung bình 3 lần) và WAPE trên tập kiểm tra cuối — thấp hơn là tốt hơn.")
            m = cv[["model", "WAPE_mean"]].merge(fm[["model", "WAPE"]], on="model").sort_values("WAPE_mean")
            fig = go.Figure()
            fig.add_trace(go.Bar(y=m.model, x=m.WAPE_mean * 100, orientation="h", name="Kiểm định chéo", marker_color=C["blue"], text=[vp(v, 2) for v in m.WAPE_mean], textposition="outside"))
            fig.add_trace(go.Bar(y=m.model, x=m.WAPE * 100, orientation="h", name="Tập kiểm tra cuối", marker_color="#8FCACA", text=[vp(v, 2) for v in m.WAPE], textposition="outside"))
            fig.update_traces(cliponaxis=False); fig.update_layout(barmode="group", xaxis_title="WAPE (%)", yaxis=dict(autorange="reversed"), xaxis_range=[0, float(max(m.WAPE.max(), m.WAPE_mean.max())) * 118])
            chart(fig, 390)
        with r:
            sec("Phát hiện chính", "Tính trực tiếp từ các tệp kết quả.")
            best_rmse = fm.sort_values("RMSE").iloc[0]
            card("Mô hình được chọn giữ vững thứ hạng", f"{winner} đứng đầu WAPE ở kiểm định chéo ({vp(wc.WAPE_mean,2)}) và trên tập kiểm tra cuối ({vp(wr.WAPE,2)}); mức tăng khi sang giai đoạn ngoài mẫu là {vn(100*(wr.WAPE-wc.WAPE_mean),2)} điểm %.", C["green"])
            st.write("")
            card("WAPE và RMSE cho kết luận khác nhau", f"Theo RMSE, {best_rmse.model} tốt nhất trên tập kiểm tra cuối ({vn(best_rmse.RMSE,3)}) — nhạy hơn với sai số lớn.", C["violet"])
            st.write("")
            if dl is not None:
                card("Khoảng dự báo thích ứng theo quy mô (Mondrian)", f"Bao phủ P10–P90 theo mức nhu cầu: {' · '.join(f'{a} {vp(b)}' for a, b in zip(dl.demand_level, dl.coverage_P10_P90))}. Tổng {vp(pm.Coverage_P10_P90.iloc[0]) if pm is not None else '—'} – vẫn thấp hơn danh nghĩa 80%.", C["amber"])
        if inv is not None:
            l, m_, r = st.columns([1, 1, 1.1])
            with l:
                sec("Nhãn bất định tồn kho", "Theo r = (P90 − P10)/(P50 + 1).")
                rk = inv.risk.value_counts().reindex(["HIGH", "MEDIUM", "LOW"]).fillna(0)
                fig = go.Figure(go.Pie(labels=rk.index, values=rk.values, hole=.7, marker=dict(colors=[RISK_COLOR[k] for k in rk.index]), sort=False, textinfo="percent"))
                fig.update_layout(annotations=[dict(text=f"<b>{vn(rk.sum())}</b><br>chuỗi", showarrow=False, font=dict(size=16))], showlegend=True)
                chart(fig, 320)
            if dq is not None:
                with m_:
                    sec("Hàng đợi phiếu khuyến nghị", "Stage 08 — theo hành động đề xuất.")
                    ac = dq.action.value_counts().reset_index(); ac.columns = ["action", "n"]
                    fig = px.bar(ac, x="n", y="action", orientation="h", text="n", color_discrete_sequence=[C["blue"]])
                    fig.update_layout(yaxis_title="", xaxis_title="Số phiếu"); chart(fig, 320)
                with r:
                    sec("Ưu tiên cao nhất", "Năm phiếu đứng đầu hàng đợi.")
                    t = dq.head(5)[["priority_rank", "store_nbr", "family", "risk", "action", "recommended_qty"]].copy()
                    t.columns = ["#", "Cửa hàng", "Nhóm", "Nhãn", "Hành động", "Số lượng"]
                    st.dataframe(t, hide_index=True, width="stretch", column_config={"Số lượng": st.column_config.NumberColumn(format="%.0f")})

# =============================================================================== 01 DATA
elif page == "01 · Dữ liệu & EDA":
    q = csv("01_data_validation/data_quality.csv"); daily = csv("01_data_validation/daily_aggregate.csv")
    promo = csv("02_eda_decomposition/promotion_descriptive.csv")
    if q is None: empty()
    else:
        c = st.columns(6)
        vals = [("Quan sát", vn(q.rows.iloc[0]), C["blue"]), ("Cửa hàng", vn(q.stores.iloc[0]), C["violet"]), ("Nhóm sản phẩm", vn(q.families.iloc[0]), C["teal"]),
                ("Chuỗi", vn(q.series.iloc[0]), C["sky"]), ("Dòng doanh số = 0", vp(q.zero_sales_share.iloc[0]), C["amber"]), ("Dòng có khuyến mãi", vp(q.promotion_row_share.iloc[0]), C["green"])]
        for col, (lab, val, tone) in zip(c, vals):
            with col: kpi(lab, val, "", tone)
        st.caption(f"Phạm vi: {q.date_min.iloc[0]} → {q.date_max.iloc[0]} · thiếu sales: {int(q.missing_sales.iloc[0])} · thiếu onpromotion: {int(q.missing_onpromotion.iloc[0])} · trùng lặp: {int(q.duplicates.iloc[0])}")
        if daily is not None:
            daily["date"] = pd.to_datetime(daily.date); d = daily.sort_values("date")
            d["ma28"] = d.sales.rolling(28, min_periods=7).mean()
            sec("Diễn biến nhu cầu toàn hệ thống", "Tổng doanh số theo ngày và trung bình trượt 28 ngày; kéo thanh bên dưới để phóng to.")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=d.date, y=d.sales, name="Doanh số ngày", line=dict(color="#8FCACA", width=1)))
            fig.add_trace(go.Scatter(x=d.date, y=d.ma28, name="Trung bình trượt 28 ngày", line=dict(color=C["blue"], width=2.6)))
            fig.update_xaxes(rangeslider=dict(visible=True, thickness=.06)); chart(fig, 430)
            l, r = st.columns(2)
            with l:
                w = d.assign(dow=d.date.dt.dayofweek).groupby("dow").sales.mean().reindex(range(7))
                lab = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
                fig = go.Figure(go.Bar(x=lab, y=w.values, marker_color=[C["violet"] if i >= 5 else "#BFE0E0" for i in range(7)], text=[vn(v) for v in w.values], textposition="outside"))
                fig.update_layout(title="Doanh số trung bình theo thứ trong tuần"); chart(fig, 360)
            with r:
                hm = d.assign(y=d.date.dt.year, m=d.date.dt.month).pivot_table(index="y", columns="m", values="sales", aggfunc="mean")
                fig = px.imshow(hm, color_continuous_scale="Teal", aspect="auto", labels=dict(x="Tháng", y="Năm", color="TB/ngày"), title="Doanh số trung bình mỗi ngày theo năm × tháng")
                chart(fig, 360)
        if promo is not None:
            sec("Doanh số theo trạng thái khuyến mãi", "Thống kê mô tả — thể hiện mối liên hệ, không phải tác động nhân quả.")
            l, r = st.columns([1.2, 1])
            with l:
                p = promo.copy(); p["Trạng thái"] = np.where(p.promo, "Có khuyến mãi", "Không khuyến mãi")
                fig = go.Figure()
                fig.add_trace(go.Bar(x=p["Trạng thái"], y=p.mean_sales, name="Trung bình", marker_color=C["blue"], text=[vn(v, 1) for v in p.mean_sales], textposition="outside"))
                fig.add_trace(go.Bar(x=p["Trạng thái"], y=p.median_sales, name="Trung vị", marker_color=C["teal"], text=[vn(v, 1) for v in p.median_sales], textposition="outside"))
                fig.update_layout(barmode="group", title="Doanh số mỗi dòng"); chart(fig, 340)
            with r:
                card("Lưu ý diễn giải", "<b>onpromotion</b> là số mặt hàng trong nhóm đang được khuyến mãi, không phải % giảm giá. Chênh lệch doanh số giữa hai nhóm còn chịu ảnh hưởng của quy mô nhóm hàng và thời gian (khuyến mãi xuất hiện nhiều hơn ở giai đoạn sau), nên không được trình bày như mức tăng do khuyến mãi.", C["amber"])

# =============================================================================== 02 STL
elif page == "02 · Phân tích chuỗi thời gian":
    x = csv("02_eda_decomposition/stl_weekly.csv")
    if x is None: empty()
    else:
        x["date"] = pd.to_datetime(x.date)
        sec("Phân rã Robust STL (period = 7)", "Tách chuỗi doanh số tổng thành xu hướng, mùa vụ tuần và phần dư; trọng số bền vững giảm ảnh hưởng ngày bất thường.")
        t = st.tabs(["Quan sát & xu hướng", "Mùa vụ tuần", "Phần dư"])
        with t[0]:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x.date, y=x.observed, name="Quan sát", line=dict(color="#BFE0E0", width=1)))
            fig.add_trace(go.Scatter(x=x.date, y=x.trend, name="Xu hướng", line=dict(color=C["blue"], width=2.8)))
            chart(fig, 440)
        with t[1]:
            l, r = st.columns([1.4, 1])
            with l:
                chart(px.line(x.tail(120), x="date", y="seasonal", title="Thành phần mùa vụ — 120 ngày cuối", color_discrete_sequence=[C["violet"]]), 380)
            with r:
                s = x.assign(dow=x.date.dt.dayofweek).groupby("dow").seasonal.mean()
                fig = go.Figure(go.Bar(x=["T2", "T3", "T4", "T5", "T6", "T7", "CN"], y=s.values, marker_color=[C["red"] if v < 0 else C["green"] for v in s.values]))
                fig.update_layout(title="Mùa vụ trung bình theo thứ"); chart(fig, 380)
        with t[2]:
            l, r = st.columns(2)
            with l: chart(px.scatter(x, x="date", y="resid", title="Phần dư theo thời gian", color_discrete_sequence=[C["slate"]]), 370)
            with r: chart(px.histogram(x, x="resid", nbins=70, title="Phân phối phần dư", color_discrete_sequence=[C["blue"]]), 370)

# =============================================================================== 03 MODELS
elif page == "03 · So sánh mô hình":
    cv = csv("04_model_comparison/rolling_cv_metrics.csv"); s = csv("04_model_comparison/model_comparison_summary.csv")
    f = csv("04_model_comparison/final_holdout_metrics.csv"); fi = csv("04_model_comparison/selected_model_feature_importance.csv")
    if cv is None or s is None: empty()
    else:
        st.markdown(f'<div class="winner"><div class="t">🏆 Kết quả lựa chọn mô hình</div><div class="n">{winner}</div>'
                    f'{pill("WAPE trung bình 3 lần kiểm định","green")}{pill("Hòa: RMSE → MAE","blue")}{pill("Tập kiểm tra cuối không dùng để chọn","amber")}</div>', unsafe_allow_html=True)
        rank = s.sort_values("WAPE_mean").reset_index(drop=True)
        l, r = st.columns([1.2, 1])
        with l:
            fig = go.Figure(go.Bar(x=rank.model, y=rank.WAPE_mean * 100, error_y=dict(type="data", array=rank.WAPE_std * 100, color="#667085"),
                                   marker_color=[C["blue"] if m == winner else "#BFE0E0" for m in rank.model], text=[vp(v, 2) for v in rank.WAPE_mean], textposition="outside"))
            fig.update_layout(title="WAPE trung bình qua 3 lần kiểm định (vạch: độ lệch chuẩn)", yaxis_title="WAPE (%)"); chart(fig, 400)
        with r:
            hm = cv.pivot(index="model", columns="fold", values="WAPE").loc[rank.model] * 100
            fig = px.imshow(hm, text_auto=".2f", color_continuous_scale="RdYlGn_r", aspect="auto", labels=dict(x="Lần kiểm định", y="", color="WAPE %"), title="WAPE (%) theo từng lần kiểm định")
            chart(fig, 400)
        t = rank[["model", "WAPE_mean", "WAPE_std", "MAE_mean", "RMSE_mean", "sMAPE_mean", "RMSLE_mean", "train_seconds_mean"]].copy()
        t.insert(0, "Hạng", range(1, len(t) + 1))
        t.columns = ["Hạng", "Mô hình", "WAPE TB", "sd WAPE", "MAE", "RMSE", "sMAPE", "RMSLE", "Giây huấn luyện"]
        t["WAPE TB"] *= 100; t["sd WAPE"] *= 100
        st.dataframe(t, hide_index=True, width="stretch", column_config={
            "WAPE TB": st.column_config.ProgressColumn("WAPE TB (%)", format="%.3f", min_value=0, max_value=float(t["WAPE TB"].max()) * 1.1),
            "sd WAPE": st.column_config.NumberColumn("sd (%)", format="%.3f"), "MAE": st.column_config.NumberColumn(format="%.2f"),
            "RMSE": st.column_config.NumberColumn(format="%.2f"), "sMAPE": st.column_config.NumberColumn(format="%.4f"),
            "RMSLE": st.column_config.NumberColumn(format="%.4f"), "Giây huấn luyện": st.column_config.NumberColumn(format="%.1f")})
        st.caption("Seasonal Naive cố định tại gốc dự báo: ngày 1–7 dùng lag_7, ngày 8–14 lag_14, ngày 15–16 lag_21 – không dùng dữ liệu trong kỳ dự báo. Random Forest huấn luyện trên 600.000 dòng vì chi phí; các mô hình khác dùng toàn bộ dữ liệu.")
        if f is not None:
            sec("Kiểm định chéo so với tập kiểm tra cuối", "Biểu đồ quả tạ: khoảng cách càng dài, sai số tăng càng nhiều khi sang giai đoạn ngoài mẫu.")
            m = s[["model", "WAPE_mean"]].merge(f[["model", "WAPE", "RMSE"]], on="model").sort_values("WAPE")
            l, r = st.columns([1.2, 1])
            with l:
                fig = go.Figure()
                for _, row in m.iterrows():
                    fig.add_trace(go.Scatter(x=[row.WAPE_mean * 100, row.WAPE * 100], y=[row.model] * 2, mode="lines", line=dict(color="#D0D5DD", width=4), showlegend=False, hoverinfo="skip"))
                fig.add_trace(go.Scatter(x=m.WAPE_mean * 100, y=m.model, mode="markers", name="Kiểm định chéo", marker=dict(size=14, color=C["blue"])))
                fig.add_trace(go.Scatter(x=m.WAPE * 100, y=m.model, mode="markers+text", name="Tập kiểm tra cuối", marker=dict(size=14, color=C["amber"]), text=[vp(v, 2) for v in m.WAPE], textposition="middle right"))
                fig.update_layout(xaxis_title="WAPE (%)", yaxis=dict(autorange="reversed")); chart(fig, 360)
            with r:
                fig = go.Figure(go.Bar(x=m.model, y=m.RMSE, marker_color=[C["violet"] if v == m.RMSE.min() else "#CFE3E6" for v in m.RMSE], text=[vn(v, 1) for v in m.RMSE], textposition="outside"))
                fig.update_layout(title="RMSE trên tập kiểm tra cuối (thấp nhất tô đậm)"); chart(fig, 360)
        if fi is not None:
            sec(f"Mức độ quan trọng đặc trưng — {winner} (mô hình được chọn)", "Gain trung bình mỗi lần tách (get_score, importance_type = gain); là chẩn đoán của mô hình, không mang nghĩa nhân quả.")
            def grp(n):
                if n.startswith("lag_"): return "Độ trễ"
                if n.startswith("roll_"): return "Thống kê trượt"
                if n in ("oil_price_lag16", "transactions_lag16", "transactions_roll28_lag16", "is_national_holiday"): return "Nguồn bổ sung"
                if n in ("store_code", "family_code", "city_code", "state_code", "type_code", "cluster"): return "Định danh"
                if n == "onpromotion": return "Khuyến mãi"
                return "Lịch"
            vcol = "gain" if "gain" in fi.columns else "importance"
            z = fi.assign(nhom=fi.feature.map(grp)).sort_values(vcol).tail(20)
            fig = px.bar(z, x=vcol, y="feature", color="nhom", orientation="h", labels={vcol: "Gain trung bình" if vcol == "gain" else "Số lần tách", "feature": "", "nhom": "Nhóm"},
                         color_discrete_sequence=[C["blue"], C["violet"], C["amber"], C["sky"], C["red"], C["green"]])
            chart(fig, 520)

# =============================================================================== 04 PROB
elif page == "04 · Dự báo xác suất":
    p = pq("05_probabilistic_forecast/probabilistic_predictions.parquet"); met = csv("05_probabilistic_forecast/probabilistic_metrics.csv")
    dl = csv("11_forecast_diagnostics/error_by_demand_level.csv")
    if p is None: empty()
    else:
        if met is not None:
            m = met.iloc[0]; c = st.columns(5)
            with c[0]: kpi("Pinball P10", vn(m.Pinball_P10, 3), "thấp hơn là tốt hơn")
            with c[1]: kpi("Pinball P50", vn(m.Pinball_P50, 3), "", C["violet"])
            with c[2]: kpi("Pinball P90", vn(m.Pinball_P90, 3), "", C["teal"])
            with c[3]: kpi("Bao phủ P10–P90", vp(m.Coverage_P10_P90, 2), "danh nghĩa 80%", C["amber"])
            with c[4]: kpi("Độ rộng trung bình", vn(m.Mean_interval_width, 2), "đơn vị/ngày", C["red"])
            st.caption(f"Phương pháp: {m.uncertainty_method}")
        sec("Biểu đồ quạt theo chuỗi", "Chọn cửa hàng và nhóm sản phẩm để xem P10/P50/P90 và doanh số thực tế của 16 ngày.")
        a, b = st.columns([.8, 1.2])
        with a: store = st.selectbox("Cửa hàng", sorted(p.store_nbr.unique()))
        with b: fam = st.selectbox("Nhóm sản phẩm", sorted(p[p.store_nbr == store].family.unique()))
        x = p[(p.store_nbr == store) & (p.family == fam)].sort_values("date")
        inside = ((x.sales >= x.p10) & (x.sales <= x.p90)).mean()
        c = st.columns(4)
        with c[0]: kpi("Tổng P50", vn(x.p50.sum()), "16 ngày")
        with c[1]: kpi("Tổng thực tế", vn(x.sales.sum()), "16 ngày", C["ink"])
        with c[2]: kpi("Bao phủ của chuỗi", vp(inside), "số ngày thực tế nằm trong khoảng", C["amber"])
        with c[3]: kpi("Độ rộng TB", vn((x.p90 - x.p10).mean(), 1), "đơn vị/ngày", C["violet"])
        chart(fan(x, f"Cửa hàng {store} · {fam}", x.sales), 440)
        sec("Hiệu chỉnh theo quy mô nhu cầu", "Khoảng Mondrian rộng dần theo quy mô dự báo điểm (9 nhóm); bao phủ được đọc theo từng mức nhu cầu và nhóm hàng.")
        l, r = st.columns(2)
        with l:
            if dl is not None:
                fig = go.Figure(go.Bar(x=dl.demand_level, y=dl.coverage_P10_P90 * 100, marker_color=[C["green"], C["teal"], C["amber"], C["red"]], text=[vp(v) for v in dl.coverage_P10_P90], textposition="outside"))
                fig.add_hline(y=80, line_dash="dash", line_color=C["ink"], annotation_text="Danh nghĩa 80%")
                fig.update_layout(title="Bao phủ P10–P90 theo mức nhu cầu", yaxis_title="%", yaxis_range=[0, 110]); chart(fig, 380)
        with r:
            fam_cov = p.assign(ins=(p.sales >= p.p10) & (p.sales <= p.p90)).groupby("family").agg(cov=("ins", "mean"), s=("sales", "mean")).reset_index().sort_values("cov")
            fig = px.bar(fam_cov, x="cov", y="family", orientation="h", color="cov", color_continuous_scale="RdYlGn", range_color=[0, 1], labels=dict(cov="Bao phủ", family=""))
            fig.add_vline(x=.8, line_dash="dash", line_color=C["ink"]); fig.update_layout(title="Bao phủ theo nhóm sản phẩm", coloraxis_showscale=False); chart(fig, 620)
        ser = p.groupby(["store_nbr", "family"]).agg(mean_sales=("sales", "mean"), width=("p90", "mean")).reset_index()
        ser["width"] = p.assign(w=p.p90 - p.p10).groupby(["store_nbr", "family"]).w.mean().values
        fig = px.scatter(ser, x=ser.mean_sales + 1, y="width", color="family", log_x=True, opacity=.65, labels=dict(x="Doanh số TB/ngày + 1 (log)", width="Độ rộng TB"), title="Độ rộng khoảng so với quy mô chuỗi")
        fig.update_layout(showlegend=False); chart(fig, 380)

# =============================================================================== 05 PROMO
elif page == "05 · Mô phỏng khuyến mãi":
    s = csv("06_promotion_scenarios/promotion_scenarios.csv")
    if s is None: empty()
    else:
        order = ["No promotion", "Low", "Current", "Medium", "High"]; lab = {"No promotion": "Không KM (0)", "Low": "Thấp (1)", "Current": "Hiện tại", "Medium": "Vừa (5)", "High": "Cao (10)"}
        agg = s.groupby("scenario").agg(p50=("p50", "mean"), chg=("conditional_change_vs_current", "mean")).reindex(order)
        cur = agg.loc["Current", "p50"]
        sec("Toàn hệ thống", "Chênh lệch P50 trung bình mỗi chuỗi so với kịch bản hiện tại (tính từ conditional_change_vs_current).")
        c = st.columns(4)
        for col, k, tone in zip(c, ["No promotion", "Low", "Medium", "High"], [C["slate"], C["teal"], C["blue"], C["violet"]]):
            with col: kpi(lab[k], (("+" if agg.loc[k, "chg"] > 0 else "") + vp(agg.loc[k, "chg"] / cur, 2)), f"P50 TB {vn(agg.loc[k, 'p50'])} · Δ {vn(agg.loc[k, 'chg'], 2)}/chuỗi", tone)
        sec("Phòng mô phỏng theo chuỗi", "Dự báo có điều kiện của mô hình được chọn khi đặt onpromotion ở các mức khác nhau cho cả 16 ngày.")
        a, b = st.columns(2)
        with a: store = st.selectbox("Cửa hàng", sorted(s.store_nbr.unique()))
        with b: fam = st.selectbox("Nhóm sản phẩm", sorted(s[s.store_nbr == store].family.unique()))
        x = s[(s.store_nbr == store) & (s.family == fam)].set_index("scenario").reindex(order).reset_index()
        cp = float(x.loc[x.scenario == "Current", "p50"].iloc[0])
        x["rel"] = np.where(cp > 0, x.conditional_change_vs_current / max(cp, 1e-9), np.nan)
        ext = (x.rel.abs() > 1).any() or cp < 1
        l, r = st.columns([1.35, 1])
        with l:
            fig = go.Figure(go.Bar(x=[lab[k] for k in x.scenario], y=x.p50, marker_color=[C["blue"] if k == "Current" else ("#FCA5A5" if abs(v) > 1 else "#8FCACA") for k, v in zip(x.scenario, x.rel.fillna(0))],
                                   error_y=dict(type="data", symmetric=False, array=x.p90 - x.p50, arrayminus=x.p50 - x.p10, color="#667085"),
                                   text=[vn(v) for v in x.p50], textposition="outside"))
            fig.update_layout(title="P50 16 ngày theo kịch bản (vạch: P10–P90; đỏ: ngoại suy > 100%)"); chart(fig, 420)
        with r:
            for _, row in x.iterrows():
                rel = row.rel
                kind = "blue" if row.scenario == "Current" else ("red" if (pd.notna(rel) and abs(rel) > 1) else ("green" if (pd.notna(rel) and rel > 0) else "gray"))
                st.markdown(f'<div class="reason">{pill(lab[row.scenario], kind)} P50 <b>{vn(row.p50)}</b> · Δ {vn(row.conditional_change_vs_current)} ({vp(rel) if pd.notna(rel) else "—"})</div>', unsafe_allow_html=True)
            if ext: st.error("Có kịch bản làm P50 thay đổi hơn 100% so với hiện tại → ngoại suy ngoài miền dữ liệu, không dùng để lập kế hoạch (POL-PROMO-004).")
            st.info("Đây là dự báo có điều kiện, không phải tác động nhân quả; onpromotion không phải % giảm giá.")
        sens = csv("12_case_studies/promotion_sensitivity_by_series.csv")
        if sens is not None:
            sec("Các chuỗi nhạy nhất", "|P50 cao − P50 hiện tại| lớn nhất — thường là ngoại suy ở nhóm hiếm có khuyến mãi.")
            t = sens.nlargest(15, "promotion_sensitivity_abs")[["store_nbr", "family", "Current", "High", "delta_High_vs_current"]]
            t.columns = ["Cửa hàng", "Nhóm", "P50 hiện tại", "P50 KM cao", "Δ"]
            st.dataframe(t, hide_index=True, width="stretch", column_config={k: st.column_config.NumberColumn(format="%.1f") for k in ["P50 hiện tại", "P50 KM cao", "Δ"]})

# =============================================================================== 06 INVENTORY
elif page == "06 · Tồn kho & Rủi ro":
    x = csv("07_inventory_decision/inventory_recommendations.csv"); a = csv("07_inventory_decision/inventory_assumptions.csv")
    if x is None: empty()
    else:
        x["r"] = (x.p90 - x.p10) / (x.p50 + 1)
        c = st.columns(5)
        with c[0]: kpi("Số chuỗi", vn(len(x)), "Store × Family")
        with c[1]: kpi("HIGH", vn((x.risk == "HIGH").sum()), "bất định tương đối cao", C["red"])
        with c[2]: kpi("MEDIUM", vn((x.risk == "MEDIUM").sum()), "", C["amber"])
        with c[3]: kpi("LOW", vn((x.risk == "LOW").sum()), "", C["green"])
        with c[4]: kpi("q*", vn(x.critical_fractile.iloc[0], 2), "Cu = 3, Co = 1 (giả định)", C["violet"])
        sec("Nhãn rủi ro phản ánh bất định tương đối", "Mỗi điểm là một chuỗi; đường nét đứt là ngưỡng r = 0,35 và 0,75. Nhãn HIGH tập trung ở chuỗi quy mô nhỏ.")
        fig = px.scatter(x, x=x.p50 + 1, y="r", color="risk", color_discrete_map=RISK_COLOR, log_x=True, log_y=True, opacity=.7,
                         hover_data=dict(store_nbr=True, family=True, p50=":.0f"), labels=dict(x="P50 16 ngày + 1 (log)", r="r (log)", risk="Nhãn"),
                         category_orders=dict(risk=["HIGH", "MEDIUM", "LOW"]))
        fig.update_yaxes(tickvals=[.01, .1, .35, .75, 1, 10, 100, 1000], ticktext=["0,01", "0,1", "0,35", "0,75", "1", "10", "100", "1000"])
        fig.update_xaxes(tickvals=[1, 10, 100, 1000, 10000, 100000], ticktext=["1", "10", "100", "1.000", "10.000", "100.000"])
        for th in (.35, .75): fig.add_hline(y=th, line_dash="dash", line_color="#667085")
        chart(fig, 430)
        l, r = st.columns(2)
        with l:
            fr = x.groupby(["family", "risk"]).size().reset_index(name="n")
            fig = px.bar(fr, x="n", y="family", color="risk", orientation="h", color_discrete_map=RISK_COLOR, category_orders=dict(risk=["HIGH", "MEDIUM", "LOW"]), labels=dict(n="Số cửa hàng", family="", risk="Nhãn"), title="Nhãn theo nhóm sản phẩm")
            chart(fig, 640)
        with r:
            fig = px.histogram(x[x.suggested_replenishment <= x.suggested_replenishment.quantile(.99)], x="suggested_replenishment", color="risk", color_discrete_map=RISK_COLOR, nbins=60,
                               category_orders=dict(risk=["HIGH", "MEDIUM", "LOW"]), labels=dict(suggested_replenishment="Lượng bổ sung gợi ý (≤ phân vị 99)", risk="Nhãn"), title="Phân phối lượng bổ sung gợi ý")
            chart(fig, 310)
            card("Công thức của Stage 07", "Vị thế giả định = 0,8 × P50 · ROP = P90 (q* ≥ 0,75) · Tồn kho an toàn = P90 − P50 · Bổ sung = max(P90 − 0,8 × P50, 0). Không có tồn kho thực, thời gian cung ứng và chi phí thật.", C["violet"])
        sec("Bảng hỗ trợ quyết định", "Lọc theo nhãn để rà soát.")
        f = st.multiselect("Nhãn", ["HIGH", "MEDIUM", "LOW"], default=["HIGH", "MEDIUM", "LOW"])
        st.dataframe(x[x.risk.isin(f)].sort_values("suggested_replenishment", ascending=False), hide_index=True, width="stretch")
        if a is not None: st.caption(a.note.iloc[0])

# =============================================================================== 07 AI DECISION CENTER
elif page == "07 · Trung tâm quyết định AI":
    path = OUT / "08_genai_decision_support" / "decision_cases.jsonl"
    dq = csv("08_genai_decision_support/decision_queue.csv")
    if not path.exists() or dq is None or "priority_rank" not in dq:
        empty(); st.info("Hãy chạy lại 08_genai_decision_support.py (phiên bản mới) để tạo hàng đợi phiếu khuyến nghị.")
    else:
        cases = _jsonl(str(path), path.stat().st_mtime); byid = {c["case_id"]: c for c in cases}
        st_ = gs.iloc[0] if gs is not None else None
        modes = json.loads(st_.mode_counts) if st_ is not None else {}
        c = st.columns(5)
        with c[0]: kpi("Phiếu trong hàng đợi", vn(len(dq)), "mọi chuỗi Store × Family")
        with c[1]: kpi("Chế độ diễn giải", "LLM + kiểm tra" if modes.get("GENAI") else "Quy tắc có căn cứ", ", ".join(f"{k}: {v}" for k, v in modes.items()), C["violet"])
        with c[2]: kpi("Vi phạm bám bằng chứng", vn(int(st_.grounding_failures)) if st_ is not None else "—", "số bản LLM bị loại", C["red"])
        with c[3]: kpi("Chuỗi lớn cần rà soát", vn(dq.reason_codes.str.contains("LARGE_SERIES").sum()), "LARGE_SERIES", C["amber"])
        with c[4]: kpi("Cảnh báo ngoại suy KM", vn(dq.promo_extrapolation.sum()), "PROMO_EXTRAPOLATION", C["teal"])

        sec("Hàng đợi ưu tiên", "Điểm = LARGE_SERIES (+3) + nhãn (HIGH +2 · MEDIUM +1 · LOW 0) + ngoại suy khuyến mãi (+1); hòa điểm xếp theo P50 giảm dần.")
        f1, f2, f3, f4 = st.columns([1, 1.2, 1.2, 1.4])
        with f1: fr = st.pills("Nhãn", ["HIGH", "MEDIUM", "LOW"], selection_mode="multi", default=["HIGH", "MEDIUM", "LOW"]) or []
        acts = sorted(dq.action.unique())
        with f2: fa = st.pills("Hành động", acts, selection_mode="multi", default=acts, format_func=lambda a: {"BỔ SUNG THẬN TRỌNG": "Thận trọng (q*)", "BỔ SUNG THEO P90": "Theo P90", "BỔ SUNG THEO P90 · RÀ SOÁT KHOẢNG DỰ BÁO": "P90 + rà soát"}.get(a, a)) or []
        with f3: fc = st.pills("Mã lý do (lọc thêm)", ["LARGE_SERIES", "PROMO_EXTRAPOLATION"], selection_mode="multi", default=[]) or []
        with f4: kw = st.text_input("Tìm cửa hàng / nhóm", placeholder="ví dụ: 45 hoặc POULTRY")
        v = dq[dq.risk.isin(fr) & dq.action.isin(fa)]
        for code in fc: v = v[v.reason_codes.str.contains(code)]
        if kw.strip():
            k = kw.strip().upper(); v = v[v.family.str.upper().str.contains(k, regex=False) | (v.store_nbr.astype(str) == k)]
        show = v[["priority_rank", "case_id", "store_nbr", "family", "risk", "priority_score", "action", "recommended_qty", "confidence", "promotion_stance"]].copy()
        show.columns = ["#", "Mã phiếu", "CH", "Nhóm", "Nhãn", "Điểm", "Hành động", "Số lượng", "Tin cậy", "Khuyến mãi"]
        st.dataframe(show.head(300), hide_index=True, width="stretch", height=280, column_config={
            "Điểm": st.column_config.ProgressColumn(format="%d", min_value=0, max_value=6), "Số lượng": st.column_config.NumberColumn(format="%.0f")})
        dl1, dl2 = st.columns([1, 3])
        with dl1:
            if not v.empty and export_ready():
                st.download_button(f"📝 Mẫu quyết định ({vn(len(v))} phiếu)", _tpl_for(tuple(v.case_id), _out_stamp()), "MAU_RA_QUYET_DINH_DU_BAO.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
        with dl2:
            st.caption("Tệp Excel: số liệu dự báo khóa, ô vàng để nhập tồn kho thực, quyết định, phương án, số lượng cuối, lý do, người duyệt; có công thức kiểm soát.")
        if v.empty:
            st.warning("Không có phiếu nào khớp bộ lọc.")
        else:
            ids = v.case_id.tolist()[:300]
            cid = st.selectbox("Mở phiếu khuyến nghị", ids, format_func=lambda i: f"#{int(dq.set_index('case_id').loc[i,'priority_rank'])} · {i}")
            cs = byid[cid]; ev = cs["evidence"]; rec = cs["recommendation"]; asg = cs["assistant"]
            conf_w = {"CAO": 90, "TRUNG BÌNH": 60, "THẤP": 30}.get(rec["confidence"], 50)
            conf_c = {"CAO": C["green"], "TRUNG BÌNH": C["amber"], "THẤP": C["red"]}.get(rec["confidence"], C["slate"])
            codes = "".join(pill(x["code"], "red" if x["code"] in ("RISK_HIGH",) else ("amber" if x["code"] in ("LARGE_SERIES", "RISK_MEDIUM") else ("violet" if x["code"] == "PROMO_EXTRAPOLATION" else "green"))) for x in cs["reason_codes"])
            L, R = st.columns([1.25, 1])
            with L:
                st.markdown(f"""<div class="dc"><div class="id">{cs['case_id']} · ƯU TIÊN #{cs['priority_rank']} · {ev['period']['start']} → {ev['period']['end']}</div>
<h2>Cửa hàng {ev['store_nbr']} · {ev['family']}</h2>{codes}{pill('Mô hình: ' + ev['selected_model'], 'blue')}
<div class="act">{rec['action']}</div><div class="qty">{vn(rec['quantity'])} <span class="sub">đơn vị bổ sung · mục tiêu {vn(rec['target'])} · phương án {rec['chosen_option']}</span></div>
<p>{asg.get('executive_summary', rec['executive_summary'])}</p>
<div class="sub" style="margin-top:12px">Mức tin cậy: <b>{rec['confidence']}</b> — {rec['confidence_reason']}</div>
<div class="meter"><div style="width:{conf_w}%;background:{conf_c}"></div></div>
<div class="sub" style="margin-top:10px">Diễn giải: {asg.get('mode_label', asg.get('mode'))} · Trạng thái: {cs['approval_status']}</div></div>""", unsafe_allow_html=True)
            with R:
                st.markdown("**Ba phương án số lượng**")
                oc = st.columns(3)
                for col, o in zip(oc, rec["options"]):
                    with col:
                        st.markdown(f'<div class="opt {"sel" if o["key"]==rec["chosen_option"] else ""}"><div class="k">PHƯƠNG ÁN {o["key"]}{" · ĐỀ XUẤT" if o["key"]==rec["chosen_option"] else ""}</div>'
                                    f'<div class="v">{vn(o["qty"])}</div><div class="s">{o["name"]}<br>mục tiêu {vn(o["target"])}</div></div>', unsafe_allow_html=True)
                st.write("")
                fig = go.Figure()
                fig.add_trace(go.Bar(x=[o["key"] for o in rec["options"]], y=[o["target"] for o in rec["options"]], marker_color=[C["blue"] if o["key"] == rec["chosen_option"] else "#BFE0E0" for o in rec["options"]], name="Mức mục tiêu"))
                fig.add_hline(y=ev["assumed_inventory_position"], line_dash="dash", line_color=C["red"], annotation_text="Vị thế giả định (0,8 × P50)")
                fig.update_layout(title="Mức mục tiêu so với vị thế tồn kho", showlegend=False, yaxis_range=[min(ev["assumed_inventory_position"], min(o["target"] for o in rec["options"])) * .9, max(o["target"] for o in rec["options"]) * 1.05])
                chart(fig, 280)
            t = st.tabs(["📈 Bằng chứng dự báo", "🏷️ Kịch bản khuyến mãi", "📚 Căn cứ chính sách (RAG)", "🧭 Cơ sở & giả định", "📝 Phiếu Markdown"])
            with t[0]:
                dd = pd.DataFrame(ev["daily"]); dd["date"] = pd.to_datetime(dd.date)
                chart(fan(dd, f"P10/P50/P90 theo ngày · {ev['family']} · CH {ev['store_nbr']}"), 380)
                c = st.columns(4)
                with c[0]: kpi("P10 kỳ", vn(ev["p10"]))
                with c[1]: kpi("P50 kỳ", vn(ev["p50"]), "", C["violet"])
                with c[2]: kpi("P90 kỳ", vn(ev["p90"]), "", C["teal"])
                with c[3]: kpi("r bất định", vn(ev["relative_uncertainty_r"], 3), f"nhãn {ev['risk']}", RISK_COLOR.get(ev["risk"], C["slate"]))
            with t[1]:
                ps = pd.DataFrame(ev["promotion_scenarios"])
                fig = go.Figure(go.Bar(x=ps.scenario, y=ps.p50, marker_color=[C["blue"] if s_ == "Current" else ("#FCA5A5" if abs(r_) > 1 else "#8FCACA") for s_, r_ in zip(ps.scenario, ps.rel_change_vs_current.replace([np.inf, -np.inf], 9))],
                                       text=[("" if s_ == "Current" else vp(r_)) if np.isfinite(r_) else "∞" for s_, r_ in zip(ps.scenario, ps.rel_change_vs_current)], textposition="outside"))
                fig.update_layout(title="P50 theo kịch bản (nhãn: thay đổi so với hiện tại)"); chart(fig, 340)
                pr = rec["promotion"]
                (st.error if pr.get("extrapolation_warning") else (st.success if pr["stance"] == "CÂN NHẮC THỬ NGHIỆM" else st.info))(f"**{pr['stance']}** — {asg.get('promotion_note', pr['text'])}")
            with t[2]:
                for s_ in cs["sources"]:
                    tags = " ".join(pill(m, "gray") for m in s_.get("matched", [])[:5])
                    src_k = pill("Quy tắc đã áp dụng", "blue") if s_.get("cited_by_rule") else pill("Truy xuất bổ sung", "gray")
                    st.markdown(f'<div class="policy">{src_k}<b>{s_.get("policy_id", "")}</b> <small>· {s_["source_id"]} · điểm {vn(s_.get("score", 0), 2)}</small><br>{s_["text"]}<br>{tags}</div>', unsafe_allow_html=True)
                st.caption("Quy định mà bộ máy quy tắc đã áp dụng được trích dẫn bắt buộc; thêm một kết quả truy xuất BM25 + tag từ knowledge_base/*.md (chính sách mẫu, giả định). Truy vấn sinh từ mã lý do của từng phiếu.")
            with t[3]:
                l_, r_ = st.columns(2)
                with l_:
                    st.markdown("**Cơ sở khuyến nghị**")
                    for x_ in asg.get("rationale", rec["rationale"]): st.markdown(f'<div class="reason">{x_}</div>', unsafe_allow_html=True)
                    st.markdown("**Giả định**")
                    for x_ in rec["assumptions"]: st.markdown(f"- {x_}")
                with r_:
                    st.markdown("**Danh mục kiểm tra trước khi phê duyệt**")
                    for i_, x_ in enumerate(rec["checklist"]): st.checkbox(x_, key=f"chk_{cid}_{i_}")
            with t[4]:
                from src.genai.decision import to_markdown
                md = to_markdown(cs)
                st.download_button("⬇️ Tải phiếu khuyến nghị (.md)", md.encode("utf-8"), f"{cid}.md", "text/markdown")
                st.markdown(md)

            sec("Phê duyệt Human-in-the-loop", "Người phê duyệt chọn quyết định, số lượng cuối cùng và lý do; mọi thao tác được ghi vào hitl_audit_log.csv (POL-HITL-001).")
            audit = OUT / "08_genai_decision_support" / "hitl_audit_log.csv"
            COLS = ["timestamp", "case_id", "store_nbr", "family", "risk", "priority_rank", "selected_model", "recommended_action", "recommended_qty",
                    "decision", "final_qty", "reviewer", "note", "assistant_mode"]
            with st.form(f"hitl_{cid}", clear_on_submit=False):
                a1, a2, a3 = st.columns([1, 1, 1])
                with a1: reviewer = st.text_input("Người phê duyệt *", placeholder="Họ tên / mã nhân viên")
                with a2: decision = st.radio("Quyết định", ["APPROVED", "ADJUSTED", "REJECTED", "REVIEW_REQUESTED"], horizontal=False,
                                             format_func=lambda z: {"APPROVED": "✓ Phê duyệt", "ADJUSTED": "✎ Phê duyệt có điều chỉnh", "REJECTED": "✕ Từ chối", "REVIEW_REQUESTED": "↻ Yêu cầu xem lại"}[z])
                with a3: final_qty = st.number_input("Số lượng cuối cùng", min_value=0.0, value=float(round(rec["quantity"])), step=1.0)
                note = st.text_area("Lý do / ghi chú *", placeholder="Ví dụ: đã đối chiếu tồn kho thực, chọn phương án B vì sức chứa kho…")
                ok = st.form_submit_button("Ghi quyết định vào nhật ký", type="primary")
            if ok:
                if not reviewer.strip() or not note.strip():
                    st.error("Cần nhập tên người phê duyệt và lý do.")
                else:
                    row = pd.DataFrame([{"timestamp": datetime.now().isoformat(timespec="seconds"), "case_id": cid, "store_nbr": ev["store_nbr"], "family": ev["family"],
                                         "risk": ev["risk"], "priority_rank": cs["priority_rank"], "selected_model": ev["selected_model"], "recommended_action": rec["action"],
                                         "recommended_qty": round(rec["quantity"], 2), "decision": decision, "final_qty": final_qty, "reviewer": reviewer.strip(),
                                         "note": note.strip(), "assistant_mode": asg.get("mode")}])
                    if audit.exists():
                        old = pd.read_csv(audit)
                        if list(old.columns) != COLS:           # chuẩn hóa về lược đồ 14 cột
                            old = old.reindex(columns=COLS)
                        pd.concat([old, row], ignore_index=True).to_csv(audit, index=False)
                    else:
                        row.to_csv(audit, index=False)
                    st.success(f"Đã ghi quyết định {decision} cho {cid}.")
            if audit.exists():
                lg = pd.read_csv(audit)
                with st.expander(f"Nhật ký kiểm toán HITL ({len(lg)} bản ghi)", expanded=False):
                    st.dataframe(lg.iloc[::-1], hide_index=True, width="stretch")
                    st.download_button("⬇️ Tải nhật ký", audit.read_bytes(), "hitl_audit_log.csv", "text/csv")
            with st.expander("Chi tiết kỹ thuật / JSON gốc"):
                st.json({k: v for k, v in cs.items() if k != "evidence"}); st.json({k: v for k, v in ev.items() if k != "daily"})

# =============================================================================== 08 DIAGNOSTICS
elif page == "08 · Phân tích sai số & Case Study":
    es = csv("11_forecast_diagnostics/error_by_series.csv"); est = csv("11_forecast_diagnostics/error_by_store.csv")
    ef = csv("11_forecast_diagnostics/error_by_family.csv"); dl = csv("11_forecast_diagnostics/error_by_demand_level.csv")
    cases = csv("12_case_studies/case_study_metrics.csv"); p = pq("05_probabilistic_forecast/probabilistic_predictions.parquet")
    if es is None: empty()
    else:
        pos = es[es.actual_sum > 0]
        c = st.columns(4)
        with c[0]: kpi("Số chuỗi", vn(len(es)), f"{vn((es.actual_sum==0).sum())} chuỗi tổng thực tế = 0")
        with c[1]: kpi("WAPE trung vị theo chuỗi", vp(pos.WAPE.median()), "chuỗi có doanh số", C["amber"])
        with c[2]: kpi("Bao phủ trung vị", vp(es.coverage_P10_P90.median()), "P10–P90 theo chuỗi", C["teal"])
        with c[3]: kpi("Bias trung vị", vn(es.bias.median(), 2), "thực tế − dự báo", C["violet"])
        if dl is not None:
            sec("Sai số theo mức nhu cầu", "WAPE giảm mạnh theo quy mô; đọc cùng độ bao phủ P10–P90 để thấy mức hiệu chuẩn của từng nhóm.")
            fig = go.Figure()
            fig.add_trace(go.Bar(x=dl.demand_level, y=dl.WAPE * 100, name="WAPE (%)", marker_color=C["blue"], text=[vp(v) for v in dl.WAPE], textposition="outside"))
            fig.add_trace(go.Scatter(x=dl.demand_level, y=dl.coverage_P10_P90 * 100, name="Bao phủ (%)", yaxis="y2", mode="lines+markers", line=dict(color=C["red"], width=3), marker=dict(size=10)))
            fig.update_traces(cliponaxis=False, selector=dict(type="bar"))
            fig.update_layout(yaxis=dict(title="WAPE (%, thang log)", type="log", tickvals=[10, 20, 50, 100, 200, 300], ticktext=["10", "20", "50", "100", "200", "300"]),
                              yaxis2=dict(title="Bao phủ (%)", overlaying="y", side="right", range=[0, 105], tickvals=[0, 20, 40, 60, 80, 100], showgrid=False))
            chart(fig, 380)
        l, r = st.columns(2)
        with l:
            if est is not None:
                x = est.sort_values("WAPE", ascending=False).head(20).assign(store=lambda d: "CH " + d.store_nbr.astype(str))
                fig = px.bar(x, x="WAPE", y="store", orientation="h", color="coverage_P10_P90", color_continuous_scale="RdYlGn", range_color=[.6, .9], labels=dict(store="", coverage_P10_P90="Bao phủ"), title="20 cửa hàng có WAPE cao nhất (màu: bao phủ)")
                fig.update_layout(yaxis=dict(autorange="reversed")); fig.update_xaxes(tickformat=".0%"); chart(fig, 520)
        with r:
            if ef is not None:
                x = ef[ef.actual_sum > 1000].sort_values("WAPE", ascending=False).head(20)
                fig = px.bar(x, x="WAPE", y="family", orientation="h", color="coverage_P10_P90", color_continuous_scale="RdYlGn", range_color=[0, 1], labels=dict(family="", coverage_P10_P90="Bao phủ"), title="Nhóm có WAPE cao nhất (tổng thực tế > 1.000)")
                fig.update_layout(yaxis=dict(autorange="reversed")); fig.update_xaxes(tickformat=".0%"); chart(fig, 520)
        if cases is not None and p is not None:
            sec("Case study chọn tự động", "du_bao_tot = WAPE thấp nhất · du_bao_kho = WAPE cao nhất · bat_dinh_cao = độ rộng khoảng lớn nhất (trong các chuỗi trên phân vị 25% quy mô) · nhay_khuyen_mai = |High − Current| lớn nhất.")
            cn = {"du_bao_tot": "Dự báo tốt", "du_bao_kho": "Dự báo khó", "bat_dinh_cao": "Độ rộng khoảng lớn nhất", "nhay_khuyen_mai": "Nhạy khuyến mãi nhất"}
            tabs = st.tabs([f"{cn.get(r_.case, r_.case)} · CH {r_.store_nbr} {r_.family}" for _, r_ in cases.iterrows()])
            for tb, (_, r_) in zip(tabs, cases.iterrows()):
                with tb:
                    x = p[(p.store_nbr == r_.store_nbr) & (p.family == r_.family)].sort_values("date")
                    a_, b_ = st.columns([2, 1])
                    with a_: chart(fan(x, f"CH {r_.store_nbr} · {r_.family}", x.sales), 360)
                    with b_:
                        kpi("WAPE", vp(r_.WAPE, 2), "", C["amber"]); st.write("")
                        kpi("Bao phủ", vp(r_.coverage_P10_P90), "", C["teal"]); st.write("")
                        kpi("Thực tế / P50", f"{vn(x.sales.sum())} / {vn(x.p50.sum())}", "tổng 16 ngày")

# =============================================================================== 09 RESEARCH
elif page == "09 · Kết quả nghiên cứu":
    obj = jsonf("09_research_summary/research_summary.json"); cv = csv("04_model_comparison/model_comparison_summary.csv"); fm = csv("04_model_comparison/final_holdout_metrics.csv")
    if not obj: empty()
    else:
        st.markdown(f'<div class="winner"><div class="t">Mô hình được lựa chọn cuối cùng</div><div class="n">{obj.get("selected_model", winner)}</div>{pill(obj.get("selection_rule", "rolling CV"), "green")}</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: card("Lựa chọn mô hình", "Mô hình thắng được chọn bằng kiểm định chéo cuốn chiếu trước tập kiểm tra cuối; tập kiểm tra cuối chỉ dùng để đánh giá độc lập.")
        with c2: card("Lượng hóa bất định", obj.get("probabilistic_method", "—"))
        with c3:
            if gs is not None: card("Lớp quyết định AI", f"{vn(gs.cases.iloc[0])} phiếu khuyến nghị · chế độ: {gs.mode_counts.iloc[0] if 'mode_counts' in gs else '—'} · mọi phiếu chờ người phê duyệt.")
        if cv is not None:
            sec("Kết quả kiểm định chéo"); st.dataframe(cv.sort_values("WAPE_mean"), hide_index=True, width="stretch")
        if fm is not None:
            sec("Kết quả tập kiểm tra cuối"); st.dataframe(fm.sort_values("WAPE"), hide_index=True, width="stretch")
        sec("Giới hạn khoa học", "Công khai để tránh diễn giải quá mức.")
        lim = list(obj.get("scientific_limits", [])) + [
            "Bao phủ P10–P90 tổng thấp hơn mức danh nghĩa 80%; cửa sổ hiệu chỉnh trùng lần kiểm định 3.",
            "Nhãn rủi ro tồn kho là chỉ báo bất định tương đối và vẫn gắn với quy mô chuỗi, không phải rủi ro kinh doanh tuyệt đối.",
            "Kịch bản khuyến mãi là dự báo có điều kiện, có ngoại suy ở nhiều chuỗi; không phải tác động nhân quả.",
            "Chưa gọi mô hình ngôn ngữ thật (chưa có khóa API): mọi phiếu ở chế độ quy tắc có căn cứ."]
        for it in lim: st.markdown(f'<div class="reason">✓ {it}</div>', unsafe_allow_html=True)
        raw = OUT / "09_research_summary" / "research_summary.json"
        st.download_button("⬇️ Tải bản tổng hợp kết quả", raw.read_bytes(), "research_summary.json")

# =============================================================================== 10 EXPORT CENTER
elif page == "10 · Xuất báo cáo & Mẫu quyết định":
    inv = csv("07_inventory_decision/inventory_recommendations.csv"); pp = pq("05_probabilistic_forecast/probabilistic_predictions.parquet")
    if inv is None or pp is None: empty()
    elif export_ready():
        from src.export.data import scope_metrics, series_in_scope
        sec("① Chọn phạm vi", "Để trống = toàn bộ. Mọi tệp xuất ra dùng cùng phạm vi này.")
        a, b_, c_ = st.columns([1, 1.6, 1])
        with a: stores = st.multiselect("Cửa hàng", sorted(inv.store_nbr.unique()), placeholder="Tất cả 54 cửa hàng")
        with b_: fams = st.multiselect("Nhóm hàng", sorted(inv.family.unique()), placeholder="Tất cả 33 nhóm hàng")
        with c_: risks = st.multiselect("Nhãn rủi ro", ["HIGH", "MEDIUM", "LOW"], placeholder="Tất cả nhãn")
        stamp = _out_stamp(); key = (tuple(int(x) for x in stores), tuple(fams), tuple(risks))
        B = _bundle(stamp); sc = _scope(*key); keys = series_in_scope(B, sc)
        if keys.empty:
            st.warning("Không có chuỗi nào trong phạm vi đã chọn.")
        else:
            m = scope_metrics(B, keys)
            k = st.columns(6)
            with k[0]: kpi("Chuỗi trong phạm vi", vn(m["series"]), f"H {m['risk_counts']['HIGH']} · M {m['risk_counts']['MEDIUM']} · L {m['risk_counts']['LOW']}")
            with k[1]: kpi("Thực tế 16 ngày", vn(m["actual_sum"]), f"{m['period'][0]} → {m['period'][1]}", C["ink"])
            with k[2]: kpi("Dự báo điểm", vn(m["point_sum"]), f"P50 {vn(m['p50_sum'])}", C["violet"])
            with k[3]: kpi("WAPE phạm vi", vp(m["WAPE"], 2), "dự báo điểm", C["amber"])
            with k[4]: kpi("Bao phủ P10–P90", vp(m["coverage"]), "danh nghĩa 80%", C["teal"])
            with k[5]: kpi("Bổ sung gợi ý", vn(m["replenishment_sum"]), "mô phỏng Stage 07", C["red"])
            sec("② Tải tệp", "Tệp được tạo trực tiếp từ outputs/ của pipeline tại thời điểm tải; không có số liệu nhập tay.")
            tag = "toan_he_thong" if sc.is_all() else "pham_vi"
            X = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            cc = st.columns(3)
            with cc[0]:
                card("📦 Workbook Excel nhiều sheet", "Bìa · KPI (kèm biểu đồ Excel) · Mô hình – CV · Kiểm tra cuối · Dự báo theo ngày · Tồn kho · Khuyến mãi · Hàng đợi quyết định · Sai số theo chuỗi. Có lọc, cố định tiêu đề, định dạng số và tô màu nhãn rủi ro.", C["blue"])
                with st.spinner("Đang tạo workbook…"):
                    st.download_button("⬇️ Tải Excel (.xlsx)", export_file("xlsx", *key, stamp), f"FAVORITA_BAO_CAO_DU_BAO_{tag}.xlsx", X, type="primary", width="stretch")
            with cc[1]:
                card("📄 Báo cáo tóm tắt 1 trang", "KPI của phạm vi, biểu đồ thực tế – P50 – P10/P90 theo ngày, nhãn rủi ro, kịch bản khuyến mãi và 10 phiếu ưu tiên. Bản HTML có nút In / Lưu PDF; bản PDF A4 dựng sẵn.", C["violet"])
                h1_, h2_ = st.columns(2)
                with h1_: st.download_button("⬇️ HTML", export_file("html", *key, stamp), f"BAO_CAO_1_TRANG_{tag}.html", "text/html", width="stretch")
                with h2_:
                    with st.spinner("Đang dựng PDF…"):
                        st.download_button("⬇️ PDF A4", export_file("pdf", *key, stamp), f"BAO_CAO_1_TRANG_{tag}.pdf", "application/pdf", width="stretch")
            with cc[2]:
                card("📝 Mẫu ra quyết định dự báo", "Mỗi dòng một chuỗi: P10/P50/P90, mục tiêu A/B/C và đề xuất (khóa); ô vàng để nhập tồn kho thực, quyết định, phương án, số lượng cuối, lý do, người duyệt. Công thức tự tính và cột Kiểm soát; sheet Tổng hợp.", C["amber"])
                with st.spinner("Đang tạo mẫu…"):
                    st.download_button("⬇️ Tải mẫu (.xlsx)", export_file("tpl", *key, stamp), f"MAU_RA_QUYET_DINH_DU_BAO_{tag}.xlsx", X, width="stretch")
            sec("③ Xem trước", "Báo cáo 1 trang và phần đầu của mẫu ra quyết định.")
            t = st.tabs(["📄 Báo cáo 1 trang", "📝 Mẫu ra quyết định", "📊 Tổng theo ngày của phạm vi"])
            with t[0]:
                _h = export_file("html", *key, stamp).decode("utf-8")
                if hasattr(st, "iframe"):
                    st.iframe(_h, height=1180)
                else:  # Streamlit cũ
                    import streamlit.components.v1 as components
                    components.html(_h, height=1180, scrolling=True)
            with t[1]:
                dq_ = csv("08_genai_decision_support/decision_queue.csv").merge(keys, on=["store_nbr", "family"]).sort_values("priority_rank")
                pv = dq_[["priority_rank", "store_nbr", "family", "risk", "p10", "p50", "p90", "chosen_option", "recommended_qty", "confidence"]].head(25).copy()
                pv.columns = ["#", "CH", "Nhóm", "Nhãn", "P10", "P50", "P90", "PA đề xuất", "SL đề xuất", "Tin cậy"]
                for col_ in ["Tồn kho thực tế", "Quyết định", "Số lượng cuối", "Lý do", "Người duyệt"]:
                    pv[col_] = ""
                st.dataframe(pv, hide_index=True, width="stretch", column_config={k_: st.column_config.NumberColumn(format="%.0f") for k_ in ["P10", "P50", "P90", "SL đề xuất"]})
                st.caption("Trong tệp Excel, các cột bên phải là ô nhập (nền vàng) có danh sách chọn: Duyệt / Điều chỉnh / Từ chối / Yêu cầu xem lại và A / B / C / Khác.")
            with t[2]:
                d_ = pp.merge(keys, on=["store_nbr", "family"]).groupby("date")[["sales", "p10", "p50", "p90"]].sum().reset_index().rename(columns={"sales": "actual"})
                chart(fan(d_, "Tổng P10/P50/P90 và thực tế của phạm vi", d_.actual), 380)

st.markdown('<div class="foot">Favorita Forecast Intelligence · Dashboard chỉ đọc đầu ra thật của pipeline, không tự tạo số liệu mô hình.</div>', unsafe_allow_html=True)
