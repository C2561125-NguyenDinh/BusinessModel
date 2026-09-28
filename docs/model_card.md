# Model card — mô hình dự báo điểm được chọn

- **Mô hình:** XGBoost toàn cục cho panel 1.782 chuỗi Store × Family (n_estimators = 450, max_depth = 8, learning_rate = 0,05, subsample = 0,8, colsample_bytree = 0,8, tree_method = hist), huấn luyện trên toàn bộ dữ liệu trước gốc dự báo.
- **Bài toán:** dự báo trực tiếp 16 ngày; 29 đặc trưng với độ trễ ≥ 16 ngày theo ngày lịch.
- **Chọn mô hình:** WAPE trung bình 3 lần kiểm định chéo cuốn chiếu (12,089%), trước khi mở tập kiểm tra cuối 31/07–15/08/2017 (WAPE 14,327%).
- **Bất định:** P10/P50/P90 bằng split-conformal Mondrian theo 9 nhóm quy mô dự báo điểm; bao phủ P10–P90 = 75,40% (danh nghĩa 80%).
- **Không dùng để:** suy luận nhân quả của khuyến mãi; tự động đặt hàng hay tự thực thi khuyến mãi. Mọi phiếu khuyến nghị cần người phê duyệt (HITL).
- Nguồn số liệu: `outputs/04_model_comparison/`, `outputs/05_probabilistic_forecast/`.
