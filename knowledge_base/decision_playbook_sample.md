# SỔ TAY QUYẾT ĐỊNH MẪU - GIẢ ĐỊNH DO NHÓM NGHIÊN CỨU SOẠN ĐỂ MINH HỌA, KHÔNG PHẢI CHÍNH SÁCH FAVORITA
# Mỗi dòng POL-... là một quy định được bộ máy khuyến nghị (Stage 08) trích dẫn khi áp dụng quy tắc tương ứng.
POL-INV-002: Khi phân vị tới hạn q* = Cu/(Cu+Co) từ 0,75 trở lên, dùng P90 làm mức tồn kho mục tiêu tham chiếu; lượng bổ sung = max(mục tiêu − vị thế tồn kho, 0). [tags: inventory, newsvendor, p90, target, replenishment]
POL-INV-003: Luôn trình bày ít nhất ba phương án số lượng (theo P50, xấp xỉ theo q*, theo P90) để người phê duyệt thấy đánh đổi giữa thiếu hàng và tồn dư. [tags: inventory, options, tradeoff, replenishment]
POL-INV-004: Chuỗi có nhu cầu dự báo thuộc nhóm lớn nhất phải được rà soát khoảng dự báo, vì độ bao phủ của khoảng P10–P90 ở nhóm quan sát nhu cầu cao nhất có thể thấp hơn mức danh nghĩa (cần đối chiếu kết quả đánh giá của lần chạy). [tags: calibration, large_series, coverage, uncertainty, review]
POL-INV-005: Chuỗi có bất định tương đối cao nhưng quy mô nhỏ ưu tiên phương án bổ sung thận trọng và theo dõi, tránh tồn dư. [tags: small_series, high_risk, uncertainty, overstock]
POL-PROMO-004: Kịch bản khuyến mãi làm P50 thay đổi quá 100% so với hiện tại được coi là ngoại suy ngoài miền dữ liệu; không dùng làm căn cứ lập kế hoạch. [tags: promotion, extrapolation, scenario, out_of_domain]
POL-PROMO-005: Kịch bản khuyến mãi chỉ là dự báo có điều kiện; mọi đề xuất tăng khuyến mãi phải qua thử nghiệm có đối chứng trước khi triển khai rộng. [tags: promotion, causal, experiment, scenario]
POL-HITL-001: Mọi phiếu khuyến nghị phải có người phê duyệt, ghi tên người phê duyệt, quyết định, số lượng cuối cùng và lý do vào nhật ký kiểm toán. [tags: human_review, approval, audit, hitl]
POL-HITL-002: Trợ lý AI chỉ diễn giải bằng chứng do quy trình dự báo tạo ra; không được tạo số liệu mới. Văn bản do mô hình ngôn ngữ sinh ra chứa số không có trong bằng chứng sẽ bị loại. [tags: genai, grounding, numbers, hallucination, guardrail]
