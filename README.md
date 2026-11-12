# 📊 Superstore Sales Analytics & AI BI Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-2.1%2B-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)
[![Gemini](https://img.shields.io/badge/Gemini-3.8%20Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)

Dự án **Bài tập lớn môn Trực quan & Phân tích Dữ liệu**: Phân tích kinh doanh toàn diện trên bộ dữ liệu bán lẻ **Kaggle Superstore Sales Dataset** (`Sample - Superstore.csv`, `9.994` dòng × `21` cột) và xây dựng hệ thống Dashboard tương tác **Streamlit** theo kiến trúc sạch (**Clean Architecture**), tích hợp **Dự báo chuỗi thời gian (Prophet / ARIMA)**, **Phân khúc khách hàng RFM**, **Phân tích giỏ hàng Apriori**, **Bản đồ địa lý Hoa Kỳ**, **Biểu đồ phân cấp Sunburst** và **Chatbot AI B2B Gemini 3.8 Flash**.

---

## 🎯 Mục tiêu & Điểm nổi bật

* **Phần 1 – Mô tả dữ liệu (10%):** Giải thích đầy đủ nguồn dữ liệu, quy mô (`9.994 × 21`), ý nghĩa 21 biến và kiểu dữ liệu thực tế.
* **Phần 2 – Khám phá & Xử lý dữ liệu / EDA (25%):** Tự động kiểm tra giá trị thiếu (`0` Null), loại bỏ `1` bản ghi trùng lặp nghiệp vụ (`Row ID = 3407`), chuẩn hóa ngày tháng (`datetime64`) & mã bưu chính (`5` ký tự), phát hiện/gắn cờ ngoại lệ theo quy tắc `1.5 × IQR` (kèm tùy chọn *IQR Winsorize*), lọc dữ liệu theo điều kiện, tổng hợp `GroupBy` và `Pivot Table`.
* **Phần 3 – Trực quan hóa dữ liệu (30%):** Đáp ứng đầy đủ 4 nhóm biểu đồ bắt buộc (**So sánh** Bar/Line, **Phân phối** Histogram/Boxplot, **Xu hướng theo thời gian**, **Tổng hợp** Grouped/Stacked Bar) cùng **Bản đồ Choropleth Hoa Kỳ** và **Sunburst / Treemap**.
* **Phần 4 – Dashboard tương tác Streamlit (25%):** Kiến trúc module hóa (`data/`, `components/`, `pages/`, `utils/`), Sidebar đa điều kiện đồng bộ bằng `st.session_state` xuyên suốt các trang, `st.tabs`/`st.expander`, tối ưu tốc độ tải bằng `@st.cache_data` và **Trợ lý AI B2B Gemini 3.8 Flash**.
* **Phần 5 – Nhận xét & Insight (10%):** Phát hiện tác động bào mòn lợi nhuận khi chiết khấu vượt ngưỡng `20%` (tỷ lệ lỗ `96.77%`), các nhóm hàng thua lỗ (`Tables`, `Bookcases`) và đề xuất giải pháp kinh doanh thực tiễn.

---

## 🏗️ Cấu trúc thư mục (Clean Architecture)

```text
btl_tqptdl/
├── Sample - Superstore.csv              # Tập dữ liệu gốc (9.994 dòng, 21 cột)
├── app.py                               # Trang chủ Dashboard Streamlit
├── eda_superstore.py                    # Script EDA: audit, làm sạch, lọc, GroupBy, Pivot, RFM, Apriori, Forecast
├── requirements.txt                     # Danh sách thư viện phụ thuộc
├── .gitignore                           # Quy tắc bỏ qua tệp tạm / môi trường ảo
├── .streamlit/
│   └── config.toml                      # Cấu hình theme giao diện Streamlit
├── data/
│   ├── __init__.py
│   ├── loader.py                        # Đọc CSV, audit, làm sạch, lọc và @st.cache_data
│   └── analytics.py                     # GroupBy, Pivot Table, Prophet/ARIMA, RFM, Apriori
├── components/
│   ├── __init__.py
│   ├── sidebar.py                       # Sidebar toàn cục đồng bộ st.session_state
│   └── ai_chatbot.py                    # Chatbot B2B Gemini 3.8 Flash (google-genai)
├── utils/
│   ├── __init__.py
│   ├── formatters.py                    # Định dạng tiền tệ/số và ánh xạ 51 mã tiểu bang Hoa Kỳ
│   └── session_state.py                 # Quản lý state toàn cục (ss_date_range, ss_regions, ...)
├── pages/
│   ├── 1_Tong_Quan_Kinh_Doanh.py        # Page 1: KPI, Grouped/Stacked, Histogram/Boxplot, RFM & Cohort Retention
│   ├── 2_Xu_Huong_Doanh_Thu.py          # Page 2: Line chart, Dự báo Prophet/ARIMA & Seasonality Heatmap
│   ├── 3_Phan_Tich_Khu_Vuc.py           # Page 3: Bar chart, multiselect, Bản đồ Mỹ & Shipping SLA
│   ├── 4_Phan_Tich_San_Pham.py          # Page 4: Top N, Sunburst/Treemap, Apriori & Pareto 80/20 (ABC)
│   └── 5_Trai_Nghiem_Nguoi_Dung.py      # Page 5: What-If Simulator, Cảnh báo lỗ, Cache, Export & Gemini AI
├── notebooks/
│   └── 01_EDA_Superstore.ipynb          # Notebook EDA & Trực quan hóa (Pandas, Matplotlib, Seaborn, Plotly)
└── docs/
    ├── Bao_cao_Du_an.md                 # Tài liệu báo cáo BTL đầy đủ 5 phần
    ├── Slide_Thuyet_Trinh.md            # Dàn ý & nội dung Slide thuyết trình (14 trang)
    └── Slide_Thuyet_Trinh.html          # Slide HTML trình chiếu / xuất PDF trực tiếp trên trình duyệt
```

---

## 👥 Phân công nhóm thực hiện (4 thành viên)

| Trang Dashboard | Tệp mã nguồn | Thành viên | Yêu cầu trực quan hóa & Tính năng chính |
| :--- | :--- | :--- | :--- |
| **Page 1** | [`pages/1_Tong_Quan_Kinh_Doanh.py`](pages/1_Tong_Quan_Kinh_Doanh.py) | *[Sinh viên 1]* | KPI (`st.metric`), **Grouped/Stacked Bar**, **Histogram & Boxplot**, **RFM** & **Cohort Retention** |
| **Page 2** | [`pages/2_Xu_Huong_Doanh_Thu.py`](pages/2_Xu_Huong_Doanh_Thu.py) | *[Sinh viên 2]* | **Xu hướng thời gian** (Plotly Line), bộ lọc động, **Dự báo Prophet/ARIMA** & **Seasonality Heatmap** |
| **Page 3** | [`pages/3_Phan_Tich_Khu_Vuc.py`](pages/3_Phan_Tich_Khu_Vuc.py) | *[Sinh viên 3]* | **So sánh khu vực** (Bar), `st.multiselect`, **Choropleth Hoa Kỳ** & **Shipping SLA** |
| **Page 4 & 5** | [`pages/4_Phan_Tich_San_Pham.py`](pages/4_Phan_Tich_San_Pham.py)<br>[`pages/5_Trai_Nghiem_Nguoi_Dung.py`](pages/5_Trai_Nghiem_Nguoi_Dung.py) | *[Sinh viên 4]* *(cùng nhóm tích hợp)* | Top N, **Sunburst/Treemap**, **Apriori**, **Pareto 80/20**, **What-If Simulator**, **Cảnh báo lỗ**, **Xuất báo cáo** & **Gemini AI Chatbot** |

---

## ⚙️ Hướng dẫn cài đặt và khởi chạy

### 1. Clone repository và tạo môi trường ảo
```bash
git clone https://github.com/namp12/btl_tqptdl.git
cd btl_tqptdl

python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Cấu hình Gemini API Key (tùy chọn cho Chatbot AI trên Page 5)
```powershell
# Windows PowerShell:
$env:GEMINI_API_KEY="your_gemini_api_key_here"
```
*(Hoặc nhập trực tiếp API Key vào ô mật khẩu trên giao diện Tab **Trợ lý AI Phân tích B2B** tại Page 5).*

### 3. Chạy kiểm tra EDA & Khởi chạy Dashboard
```bash
# Chạy script EDA (kiểm tra chất lượng, làm sạch, GroupBy, Pivot, RFM, Apriori, Forecast)
python eda_superstore.py

# Khởi chạy ứng dụng Streamlit Dashboard
streamlit run app.py
```

---

## 📚 Tài liệu & Sản phẩm nộp kèm
* **Báo cáo chi tiết 5 phần:** [`docs/Bao_cao_Du_an.md`](docs/Bao_cao_Du_an.md)
* **Notebook EDA tương tác:** [`notebooks/01_EDA_Superstore.ipynb`](notebooks/01_EDA_Superstore.ipynb)
* **Slide thuyết trình (14 trang):** [`docs/Slide_Thuyet_Trinh.md`](docs/Slide_Thuyet_Trinh.md) | Trình chiếu trực tiếp / Xuất PDF: [`docs/Slide_Thuyet_Trinh.html`](docs/Slide_Thuyet_Trinh.html)
