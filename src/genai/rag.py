"""Truy xuất chính sách (RAG nhẹ, không cần thư viện ngoài).

- Mỗi dòng chính sách trong knowledge_base/*.md có dạng
  `POL-XXX-000: nội dung ... [tags: tu_khoa_1, tu_khoa_2]` là một đoạn (chunk).
- Điểm liên quan = BM25 trên token đã bỏ dấu tiếng Việt + thưởng khi trùng tag.
- Giữ tương thích hàm cũ `retrieve(query, kb_dir)` (trả về list dict source_id/text).
"""
from __future__ import annotations
import math, re, unicodedata
from pathlib import Path

_POL = re.compile(r"^\s*(?:[-*]\s*)?(POL-[A-Z]+-\d+)\s*:\s*(.+?)\s*(?:\[tags?:\s*(.+?)\])?\s*$")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d")


def _tok(s: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9_]+", _norm(s)) if len(t) > 1]


def load_chunks(kb_dir) -> list[dict]:
    chunks = []
    for p in sorted(Path(kb_dir).glob("*.md")):
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            m = _POL.match(line)
            if not m:
                continue
            pid, text, tags = m.group(1), m.group(2).strip(), (m.group(3) or "")
            tag_list = [_norm(t.strip()) for t in tags.split(",") if t.strip()]
            chunks.append({"policy_id": pid, "source_id": f"{p.name}#L{i}", "text": text,
                           "tags": tag_list, "tokens": _tok(text) + tag_list})
    return chunks


def search(query: str, kb_dir, k: int = 4, tags: list[str] | None = None) -> list[dict]:
    """Trả về tối đa k chính sách liên quan nhất kèm điểm và lý do khớp."""
    chunks = load_chunks(kb_dir)
    if not chunks:
        return [{"policy_id": "NO_KB", "source_id": "NO_MATCH", "text": "Không tìm thấy kho chính sách.", "score": 0.0, "matched": []}]
    q = _tok(query)
    want = {_norm(t) for t in (tags or [])}
    n = len(chunks)
    avg = sum(len(c["tokens"]) for c in chunks) / n
    df = {}
    for c in chunks:
        for t in set(c["tokens"]):
            df[t] = df.get(t, 0) + 1
    res = []
    for c in chunks:
        tf = {}
        for t in c["tokens"]:
            tf[t] = tf.get(t, 0) + 1
        s = 0.0
        hit = []
        for t in set(q):
            if t in tf:
                idf = math.log(1 + (n - df[t] + .5) / (df[t] + .5))
                s += idf * tf[t] * 2.2 / (tf[t] + 1.2 * (.25 + .75 * len(c["tokens"]) / avg))
                hit.append(t)
        tag_hit = sorted(want & set(c["tags"]))
        s += 1.5 * len(tag_hit)
        if s > 0:
            res.append({"policy_id": c["policy_id"], "source_id": c["source_id"], "text": c["text"],
                        "score": round(s, 3), "matched": tag_hit + [h for h in hit if h not in tag_hit][:6]})
    res.sort(key=lambda x: (-x["score"], x["policy_id"]))
    return res[:k] or [{"policy_id": "NO_MATCH", "source_id": "NO_MATCH", "text": "Không tìm thấy chính sách liên quan.", "score": 0.0, "matched": []}]


def retrieve(query, kb_dir, k: int = 4):
    """API cũ (được tests/test_core.py sử dụng)."""
    return [{"source_id": r["source_id"], "text": r["text"]} for r in search(query, kb_dir, k)]
