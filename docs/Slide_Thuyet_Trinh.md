# DÀN Ý & NỘI DUNG SLIDE THUYẾT TRÌNH (14 SLIDES)
**Đề tài:** Xây dựng Hệ thống Phân tích & Trực quan hóa Dữ liệu Bán lẻ Superstore với Streamlit

---

### Slide 1: Trang bìa (Title Slide)
* **Tên đề tài:** Phân tích Dữ liệu Kinh doanh & Xây dựng Dashboard Tương tác Superstore
* **Công nghệ sử dụng:** Python, Pandas, Plotly, Streamlit, GitHub
* **Nhóm thực hiện:** [Tên nhóm / Danh sách 5 thành viên phụ trách Page 1–5]

---

### Slide 2: Giới thiệu bài toán khách hàng (Business Problem)
* **Bối cảnh:** Chuỗi bán lẻ Superstore tại Hoa Kỳ vận hành hàng nghìn giao dịch mỗi năm trên 4 khu vực và 3 ngành hàng lớn.
* **Vấn đề đặt ra:** Ban lãnh đạo chưa có công cụ trực quan theo thời gian thực để trả lời:
  * Doanh thu và lợi nhuận biến động thế nào qua các năm/quý?
  * Khu vực và danh mục sản phẩm nào đang sinh lời hoặc gây thua lỗ?
  * Chính sách chiết khấu ảnh hưởng ra sao đến biên lợi nhuận?
* **Mục tiêu:** Xây dựng Dashboard BI 5 trang hỗ trợ ra quyết định nhanh và chính xác.

---

### Slide 3: Mô tả dữ liệu (Dataset Overview)
* **Nguồn dữ liệu:** Kaggle — *Superstore Sales Dataset* (`Sample - Superstore.csv`).
* **Quy mô:** `9.994` dòng × `21` cột (giai đoạn 2014–2017, `5.009` đơn hàng, `793` khách hàng, `1.862` sản phẩm).
* **4 nhóm biến chính:**
  * Thông tin đơn hàng (`Row ID`, `Order ID`, `Order Date`).
  * Khách hàng & Giao hàng (`Customer ID`, `Segment`, `Ship Mode`, `Region`, `State`, `City`, `Postal Code`).
  * Sản phẩm (`Product ID`, `Category`, `Sub-Category`, `Product Name`).
  * Chỉ số tài chính (`Sales`, `Quantity`, `Discount`, `Profit`).

---

### Slide 4: Quy trình làm sạch & Xử lý dữ liệu (EDA — 25%)
* **Kiểm tra dữ liệu thiếu & bảng mã:** Đọc tệp với `windows-1252`; ghi nhận `0` giá trị thiếu (Null).
* **Xử lý trùng lặp:** Loại bỏ `1` bản ghi trùng lặp nghiệp vụ (tại `Row ID = 3407`), còn `9.993` dòng sạch.
* **Chuẩn hóa kiểu dữ liệu:** Chuyển `Order Date`, `Ship Date` sang `datetime`; `Postal Code` sang chuỗi 5 ký tự; tính thêm `Shipping_Days` và `Profit_Margin_Pct`.
* **Xử lý ngoại lệ (IQR):** Gắn cờ ngoại lệ cho `Sales` (1.167 điểm) và `Profit` (1.881 điểm), kết hợp tùy chọn Winsorize trên Sidebar để không làm mất dữ liệu giao dịch B2B thực tế.

---

### Slide 5: Tổng hợp thống kê (GroupBy & Pivot Table)
* **GroupBy theo Năm:** Doanh thu tăng từ `484.2K USD` (2014) lên `733.2K USD` (2017).
* **GroupBy theo Khu vực:** `West` (`725.5K USD`) và `East` (`678.8K USD`) dẫn đầu; `Central` biên lợi nhuận thấp nhất (`7.92%`).
* **Pivot Table (`Region × Category` & `Year × Segment`):** Nhận diện ngay cơ cấu đóng góp doanh thu của từng ngành hàng tại từng khu vực và tốc độ tăng trưởng số đơn hàng theo phân khúc.

---

### Slide 6: Kiến trúc hệ thống Dashboard Streamlit (Clean Architecture)
* **Tách module chuyên nghiệp 4 tầng:**
  * `data/`: `loader.py` (CSV, audit, làm sạch, `@st.cache_data`) & `analytics.py` (GroupBy, Pivot, Prophet/ARIMA, RFM, Apriori).
  * `components/`: `sidebar.py` (đồng bộ `st.session_state`) & `ai_chatbot.py` (Gemini 3.8 Flash).
  * `utils/`: `formatters.py` (USPS state codes, USD) & `session_state.py` (giữ nguyên bộ lọc khi chuyển trang).
  * `pages/`: 5 trang độc lập cho 5 thành viên.

---

### Slide 7: Page 1 — Tổng quan kinh doanh & Phân khúc RFM
* **Mục tiêu:** Theo dõi KPI tức thời và phân loại khách hàng để có chiến lược chăm sóc phù hợp.
* **Kỹ thuật:** `st.metric` (Doanh thu `~2.30 triệu USD`, Đơn hàng `5.009`, Số lượng `37,873`, Biên LN `12.47%`) + **Mô hình RFM** tự động gắn nhãn *VIP*, *Khách hàng trung thành*, *Khách hàng mới*, *Nguy cơ rời bỏ*.
* **Insight:** Phân khúc `Consumer` đóng góp 50.56% doanh thu; nhóm *Nguy cơ rời bỏ* cần chiến dịch giữ chân sớm.

---

### Slide 8: Page 2 — Xu hướng doanh thu & Dự báo (Prophet / ARIMA)
* **Mục tiêu:** Theo dõi tính mùa vụ lịch sử và dự báo doanh thu 3–6 tháng tiếp theo.
* **Kỹ thuật:** Biểu đồ đường **Plotly** (`st.date_input` + `st.slider`), tích hợp mô hình **Prophet (Meta) / ARIMA** vẽ đường nét đứt dự báo kèm dải tin cậy.
* **Insight:** Doanh thu đạt đỉnh vào Quý 4 hằng năm (tháng 11–12) và mô hình dự báo xu hướng tiếp tục tăng trưởng ổn định.

---

### Slide 9: Page 3 — Phân tích khu vực & Bản đồ Địa lý Hoa Kỳ
* **Mục tiêu:** So sánh hiệu suất 4 vùng và quan sát phân bố trực tiếp trên bản đồ từng tiểu bang.
* **Kỹ thuật:** Biểu đồ cột **Plotly** + `st.multiselect` đa khu vực + **Bản đồ Choropleth Hoa Kỳ** (`locationmode="USA-states"`) hỗ trợ zoom và hover chi tiết.
* **Insight:** `West` & `East` dẫn đầu lợi nhuận; một số bang thuộc `Central` (như Texas) lỗ nặng do chiết khấu cao.

---

### Slide 10: Page 4 — Sản phẩm (Top N), Sunburst & Giỏ hàng (Apriori)
* **Mục tiêu:** Xác định sản phẩm chủ lực, khoan sâu phân cấp và tìm cơ hội bán chéo.
* **Kỹ thuật:** Top N theo thời gian/khu vực + **Biểu đồ Sunburst/Treemap** click drill-down (`Category → Sub-Category → Product Name`) + **Thuật toán Apriori** tính Support/Confidence/Lift.
* **Insight:** `Copiers` và `Phones` sinh lời cao nhất; `Tables` (`-17.7K USD`) lỗ nặng; thuật toán Apriori gợi ý các cặp mua kèm giá trị cho chiến dịch cross-sell.

---

### Slide 11: Page 5 — Trải nghiệm người dùng, Cache & Chatbot AI Gemini
* **Mục tiêu:** Tối ưu UX và cung cấp trợ lý phân tích dữ liệu tức thời cho Ban Giám đốc.
* **Kỹ thuật:**
  * Toàn bộ bộ lọc đặt tại **Sidebar** và đồng bộ bằng **`st.session_state`** giữa mọi trang.
  * Phân tầng nội dung gọn gàng bằng **`st.tabs`** và **`st.expander`** + **`@st.cache_data`**.
  * Tích hợp **Chatbot AI Gemini 3.8 Flash** (`google-genai`) tự đọc ngữ cảnh DataFrame đang lọc để trả lời câu hỏi tự nhiên.

---

### Slide 12: Phát hiện trọng tâm — Tác động của Chiết khấu (Discount)
* **Phân tích dữ liệu thực nghiệm:**
  * `Discount = 0%`: Lợi nhuận trung bình `+66.90 USD/giao dịch`, tỷ lệ lỗ `0%`.
  * `Discount > 0%`: Lợi nhuận trung bình `-6.66 USD/giao dịch`, tỷ lệ lỗ `36.01%`.
  * `Discount > 20%`: Lợi nhuận trung bình `-97.18 USD/giao dịch`, **96.77% giao dịch bị lỗ**.
* **Kết luận:** Ngưỡng chiết khấu trên `20%` là nguyên nhân cốt lõi bào mòn lợi nhuận của doanh nghiệp.

---

### Slide 13: Đề xuất giải pháp kinh doanh
1. **Kiểm soát trần chiết khấu ở mức 20%:** Yêu cầu phê duyệt cấp quản lý đối với mọi mức giảm giá > 20%.
2. **Tái cấu trúc nhóm `Tables` & `Bookcases`:** Đàm phán lại chi phí vận chuyển/giá vốn hoặc bán theo gói combo kèm sản phẩm biên lợi nhuận cao.
3. **Tập trung cải thiện vùng `Central`:** Giảm tần suất khuyến mãi sâu tại các tiểu bang thuộc khu vực Central.
4. **Đẩy mạnh bán chéo phân khúc `Home Office` & `Corporate`:** Tăng tỷ trọng thiết bị công nghệ (`Technology`) có biên lợi nhuận `17.4%`.

---

### Slide 14: Tổng kết & Q&A
* **Kết quả đạt được:** Hoàn thành quy trình EDA bằng Pandas, xây dựng Dashboard Streamlit 5 trang liên kết chặt chẽ, lưu trữ mã nguồn chuẩn hóa trên GitHub kèm báo cáo đầy đủ.
* **Hướng phát triển:** Tích hợp mô hình dự báo doanh thu chuỗi thời gian (Prophet/ARIMA) và cảnh báo tự động các đơn hàng lỗ.
* **Cảm ơn thầy/cô và các bạn đã lắng nghe!**

