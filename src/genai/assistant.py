"""Lớp diễn giải bằng mô hình ngôn ngữ (tùy chọn) có kiểm tra bám bằng chứng.

- Không có OPENAI_API_KEY → chế độ RULE_BASED: dùng nguyên văn phiếu do bộ máy quy tắc tạo.
- Có khóa → gọi LLM để viết lại phần diễn giải (tóm tắt, cơ sở, ghi chú khuyến mãi).
  Mọi con số trong văn bản LLM phải khớp một con số trong bằng chứng (sai lệch ≤ 0,5%),
  nếu không bản LLM bị loại và quay về bản quy tắc (POL-HITL-002).
"""
from __future__ import annotations
import json, os, re

NUM = re.compile(r"(?<![\w.,])[−-]?\d{1,3}(?:\.\d{3})+(?:,\d+)?|(?<![\w.,])[−-]?\d+(?:,\d+)?")


def _to_float(tok: str) -> float:
    t = tok.replace("−", "-")
    if re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+(?:,\d+)?", t):
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", ".")
    return float(t)


def _numbers_in(obj) -> list[float]:
    out = []
    def walk(o):
        if isinstance(o, bool): return
        if isinstance(o, (int, float)): out.append(float(o)); return
        if isinstance(o, str):
            for m in NUM.finditer(o):
                try: out.append(_to_float(m.group()))
                except ValueError: pass
            return
        if isinstance(o, dict): [walk(v) for v in o.values()]
        if isinstance(o, list): [walk(v) for v in o]
    walk(obj)
    return out


def grounding_check(text_fields: dict, evidence: dict, draft: dict) -> dict:
    allowed = _numbers_in(evidence) + _numbers_in(draft)
    allowed_pct = [100 * a for a in allowed]
    bad = []
    for v in _numbers_in(text_fields):
        if abs(v) <= 31:   # số thứ tự, ngày trong tháng, số ngày kỳ dự báo
            continue
        ok = any(abs(v - a) <= max(.5, .005 * abs(a)) for a in allowed + allowed_pct)
        if not ok: bad.append(v)
    return {"passed": not bad, "unsupported_numbers": bad[:10]}


def load_env(root):
    p = root / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                if v.strip() and not os.getenv(k.strip()): os.environ[k.strip()] = v.strip()


def rule_based(draft: dict, reason: str = "Không có OPENAI_API_KEY") -> dict:
    return {"mode": "RULE_BASED", "mode_label": "Bộ máy quy tắc có căn cứ (chưa dùng LLM)", "reason": reason,
            "executive_summary": draft["executive_summary"], "rationale": draft["rationale"],
            "promotion_note": draft["promotion"]["text"], "grounding": {"passed": True, "unsupported_numbers": []}}


PROMPT = """Bạn là trợ lý hỗ trợ ra quyết định bán lẻ. Viết lại phần diễn giải của phiếu khuyến nghị bằng tiếng Việt,
văn phong chuyên nghiệp, ngắn gọn. QUY TẮC BẮT BUỘC:
1) Chỉ dùng số liệu có trong EVIDENCE hoặc DRAFT; không tạo số mới; định dạng số kiểu Việt Nam.
2) Không đổi hành động, phương án, số lượng, mức tin cậy của DRAFT.
3) Không diễn giải kịch bản khuyến mãi là tác động nhân quả hay % giảm giá.
4) Nhắc rằng quyết định cần người phê duyệt.
Trả về JSON với đúng các khóa: "executive_summary" (≤ 90 từ), "rationale" (danh sách 3–5 câu), "promotion_note" (≤ 60 từ).
"""


def explain(evidence: dict, draft: dict, sources: list, model: str = "gpt-5-mini") -> dict:
    if not os.getenv("OPENAI_API_KEY"):
        return rule_based(draft)
    try:
        from openai import OpenAI
        slim = {k: v for k, v in evidence.items() if k != "daily"}
        payload = json.dumps({"EVIDENCE": slim, "DRAFT": {k: draft[k] for k in ("action", "quantity", "target", "confidence", "executive_summary", "rationale", "promotion")},
                              "POLICY_SOURCES": sources}, ensure_ascii=False, default=str)
        r = OpenAI(timeout=90).responses.create(model=model, input=PROMPT + "\n" + payload)
        txt = re.sub(r"^```(?:json)?|```$", "", r.output_text.strip()).strip()
        obj = json.loads(txt)
        fields = {"executive_summary": str(obj["executive_summary"]), "rationale": [str(x) for x in obj["rationale"]],
                  "promotion_note": str(obj["promotion_note"])}
        g = grounding_check(fields, evidence, draft)
        if not g["passed"]:
            out = rule_based(draft, "Bản LLM bị loại do chứa số không có trong bằng chứng")
            out["grounding"] = g; out["mode"] = "RULE_BASED_AFTER_GUARDRAIL"
            return out
        return {"mode": "GENAI", "mode_label": f"LLM ({model}) viết lại diễn giải, đã qua kiểm tra bám bằng chứng",
                "reason": "", **fields, "grounding": g}
    except Exception as e:  # lỗi mạng/khóa/định dạng → an toàn quay về quy tắc
        out = rule_based(draft, f"Lỗi khi gọi LLM: {type(e).__name__}")
        out["mode"] = "RULE_BASED_AFTER_ERROR"
        return out


# giữ tương thích tên hàm cũ
def fallback(evidence, sources):
    return {"mode": "RULE_BASED", "recommended_action": "Human review trước khi phê duyệt.", "approval_status": "PENDING"}
