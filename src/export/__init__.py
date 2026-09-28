"""Xuất dữ liệu và báo cáo từ đầu ra thật của pipeline (không tạo số liệu mới).

- excel_report.build_workbook(...)      -> bytes (.xlsx nhiều sheet có định dạng và biểu đồ gốc Excel)
- decision_template.build_template(...) -> bytes (.xlsx mẫu ra quyết định cho người lập kế hoạch)
- report.build_html(...) / build_pdf(...) -> báo cáo tóm tắt 1 trang (HTML in được / PDF A4)
"""
from .data import Scope, load_bundle, apply_scope  # noqa: F401
