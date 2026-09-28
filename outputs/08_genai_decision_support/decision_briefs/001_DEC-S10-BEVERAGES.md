# PHIẾU KHUYẾN NGHỊ DEC-S10-BEVERAGES

**Cửa hàng 10 – BEVERAGES** · Kỳ 16 ngày (2017-07-31 → 2017-08-15) · Mô hình: XGBoost
**Ưu tiên:** #1 (điểm 5) · **Nhãn:** HIGH · **Tin cậy:** THẤP · **Trạng thái:** PENDING_HUMAN_REVIEW

## 1. Tóm tắt điều hành
Nhu cầu 16 ngày của cửa hàng 10 – BEVERAGES có trung vị (P50) 22.173 đơn vị, khoảng P10–P90 từ 16.083 đến 33.099. Khuyến nghị: bổ sung theo mức P90 và rà soát lại khoảng dự báo, bổ sung 15.361 đơn vị để đạt mức mục tiêu 33.099 (phương án C), với vị thế tồn kho giả định 17.738. Mức tin cậy: thấp.

## 2. Khuyến nghị tồn kho — BỔ SUNG THEO P90 · RÀ SOÁT KHOẢNG DỰ BÁO

| Phương án | Mức mục tiêu | Số lượng bổ sung | Đánh đổi |
|---|---:|---:|---|
| A. Theo P50 (trung vị) | 22.173 | 4.435 | Tồn dư thấp nhất; xác suất thiếu hàng khoảng 50% theo mô hình. |
| B. Theo q* = 0,75 (xấp xỉ P75) | 29.002 | 11.264 | Cân bằng theo tỷ lệ chi phí Cu/Co; giá trị phân vị là xấp xỉ nội suy giữa P50 và P90. |
| C. Theo P90 (bảo thủ) ✅ | 33.099 | 15.361 | Giảm nguy cơ thiếu hàng; chấp nhận tồn dư cao hơn. |

## 3. Khuyến mãi — KHÔNG ĐỀ XUẤT TĂNG
Không có kịch bản khuyến mãi nào trong miền tin cậy làm P50 tăng đáng kể (> 2%); chưa có cơ sở đề xuất tăng khuyến mãi.

| Kịch bản | P50 | Chênh lệch so với hiện tại |
|---|---:|---:|
| No promotion | 19.894 | −2.172 (−9,8%) |
| Current | 22.066 | 0 (0,0%) |
| Low | 20.156 | −1.911 (−8,7%) |
| Medium | 20.300 | −1.767 (−8,0%) |
| High | 20.553 | −1.513 (−6,9%) |

## 4. Cơ sở khuyến nghị
- Nhãn bất định tương đối HIGH (r = (P90 − P10)/(P50 + 1) = 0,767).
- Chuỗi quy mô lớn (P50 trung bình 1.385,8/ngày ≥ 282,6, là phân vị 75% của P50 theo ngày trên toàn bộ 1.782 chuỗi): khoảng dự báo có thể quá hẹp so với quy mô. Trên tập kiểm tra của lần chạy, độ bao phủ P10–P90 ở nhóm quan sát nhu cầu cao nhất chỉ 72,8%.
- Phân vị tới hạn q* = Cu/(Cu + Co) = 0,75; mức mục tiêu tham chiếu theo quy định POL-INV-002.
- Ngày có P50 cao nhất trong kỳ: Thứ Bảy 05/08/2017 (1.835,5 đơn vị) — ưu tiên bảo đảm hàng trước ngày này.

## 5. Căn cứ chính sách (truy xuất RAG)
- **POL-INV-004** (decision_playbook_sample.md#L5): Chuỗi có nhu cầu dự báo thuộc nhóm lớn nhất phải được rà soát khoảng dự báo, vì độ bao phủ của khoảng P10–P90 ở nhóm quan sát nhu cầu cao nhất có thể thấp hơn mức danh nghĩa (cần đối chiếu kết quả đánh giá của lần chạy).
- **POL-INV-002** (decision_playbook_sample.md#L3): Khi phân vị tới hạn q* = Cu/(Cu+Co) từ 0,75 trở lên, dùng P90 làm mức tồn kho mục tiêu tham chiếu; lượng bổ sung = max(mục tiêu − vị thế tồn kho, 0).
- **POL-INV-003** (decision_playbook_sample.md#L4): Luôn trình bày ít nhất ba phương án số lượng (theo P50, xấp xỉ theo q*, theo P90) để người phê duyệt thấy đánh đổi giữa thiếu hàng và tồn dư.
- **POL-INV-001** (promotion_policy_sample.md#L5): Các quyết định tồn kho chỉ là mô phỏng khi inventory position và lead time do người dùng nhập.
- **POL-PROMO-002** (promotion_policy_sample.md#L3): Không diễn giải thay đổi `onpromotion` là % giảm giá.
- **POL-HITL-001** (decision_playbook_sample.md#L9): Mọi phiếu khuyến nghị phải có người phê duyệt, ghi tên người phê duyệt, quyết định, số lượng cuối cùng và lý do vào nhật ký kiểm toán.
- **POL-PROMO-001** (promotion_policy_sample.md#L2): Kịch bản có độ bất định cao phải chuyển Human Review.

## 6. Giả định
- Vị thế tồn kho = 0,8 × P50 = 17.738 (giả định của Stage 07, không phải tồn kho thực).
- Chi phí thiếu hàng Cu = 3, chi phí tồn dư Co = 1 (giả định kịch bản).
- P10/P50/P90 của kỳ là tổng của 16 phân vị theo ngày — mang tính mô tả, không phải phân vị chính xác của tổng nhu cầu.
- Không có dữ liệu giá bán, biên lợi nhuận và thời gian cung ứng.

## 7. Danh mục kiểm tra trước khi phê duyệt
- [ ] Đối chiếu vị thế tồn kho thực tế (hiện đang dùng giả định 0,8 × P50) và hàng đang về.
- [ ] Rà soát lại khoảng dự báo: với chuỗi lớn, khoảng P10–P90 có thể hẹp hơn biến động thực tế.
- [ ] Xác nhận thời gian cung ứng và lịch giao hàng của nhà cung cấp.
- [ ] Kiểm tra sức chứa kho và hạn sử dụng (đặc biệt với hàng tươi sống).
- [ ] Chọn phương án số lượng A/B/C hoặc nhập số lượng khác, ghi rõ lý do.

---
*Chế độ tạo diễn giải: RULE_BASED. Trợ lý AI không tạo số liệu dự báo; mọi con số lấy từ đầu ra của quy trình. Quyết định cuối cùng thuộc về người phê duyệt.*