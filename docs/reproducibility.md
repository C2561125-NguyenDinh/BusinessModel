# Tái lập

1. Đặt dữ liệu Kaggle vào `data/raw/`.
2. Chạy `START_WINDOWS.bat` (Stage 01 → 14, rồi mở dashboard). SEED = 42.
3. Lần chạy chính thức dùng Python 3.11, pandas 2.3.3, numpy 2.4.4, scikit-learn 1.8.0, xgboost 3.2.0, lightgbm 4.7.0, statsmodels 0.15.0 (2 CPU, 53,0 phút). Nếu `.venv` cài phiên bản khác (ví dụ xgboost 3.4.1, scikit-learn 1.9.1), XGBoost và Random Forest có thể lệch nhỏ.
4. Kiểm thử: `10_pipeline_smoke_test.py` (chạy trong pipeline), `pytest tests`, dashboard `streamlit run app.py`.
