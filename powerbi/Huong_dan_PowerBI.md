# Hướng dẫn dựng file Power BI (`.pbix`) cho Dự án Superstore

Thư mục `powerbi/` cung cấp sẵn bộ cấu hình để bạn tạo nhanh tệp `Superstore_Dashboard.pbix` đồng bộ giao diện và số liệu với ứng dụng Streamlit:
* [`power_query.m`](power_query.m): Script nạp và làm sạch `Sample - Superstore.csv` (xử lý encoding `1252`, locale `en-US`, loại 1 dòng trùng lặp, tạo biến thời gian & `Shipping Days`).
* [`measures.dax`](measures.dax): Bộ công thức DAX chuẩn (`Total Sales`, `Total Profit`, `Profit Margin %`, `Total Orders`, `Sales YoY %`, ...).
* [`theme_superstore.json`](theme_superstore.json): Theme màu sắc và bo góc đồng nhất với Dashboard Streamlit.

---

## Bước 1: Cài đặt Power BI Desktop (Miễn phí)
* Mở **Microsoft Store** trên Windows, tìm **Power BI Desktop** và bấm **Install / Get** (hoặc tải bộ cài từ trang chủ Microsoft).

## Bước 2: Nạp dữ liệu & Làm sạch bằng Power Query
1. Mở Power BI Desktop → chọn **Get data → Blank query** (hoặc **Text/CSV** chọn `Sample - Superstore.csv`).
2. Vào **Home → Transform data** để mở Power Query Editor.
3. Chọn **Home → Advanced Editor**, dán toàn bộ nội dung tệp [`power_query.m`](power_query.m) vào (kiểm tra đúng đường dẫn tới `Sample - Superstore.csv`) → bấm **Done**.
4. Đổi tên bảng thành `Sample - Superstore` → bấm **Close & Apply**.

## Bước 3: Áp dụng Theme & Tạo bảng Ngày (`DimDate`) + Measures
1. Vào tab **View → Themes (mũi tên xuống) → Browse for themes** → chọn [`theme_superstore.json`](theme_superstore.json).
2. Tạo bảng lịch (`Modeling → New table`):
   ```dax
   DimDate =
   ADDCOLUMNS (
       CALENDAR ( DATE ( 2014, 1, 1 ), DATE ( 2017, 12, 31 ) ),
       "Year", YEAR ( [Date] ),
       "Quarter", "Q" & FORMAT ( [Date], "q" ),
       "Month Number", MONTH ( [Date] ),
       "Month Name", FORMAT ( [Date], "MMM" ),
       "YearMonth", FORMAT ( [Date], "YYYY-MM" )
   )
   ```
3. Vào **Model view**, kéo nối `DimDate[Date]` → `'Sample - Superstore'[Order Date]` (quan hệ `1:*`).
4. Tạo các Measures theo danh sách trong [`measures.dax`](measures.dax).

## Bước 4: Dựng 4 Trang Dashboard (Phân công 4 sinh viên)
* **Trang 1 – Tổng quan & Phân phối (SV 1):**
  * 4 thẻ **Card** (`Total Sales`, `Total Profit`, `Total Orders`, `Total Quantity`).
  * **Stacked Bar Chart** (`Segment` × `Category` theo `Total Sales`).
  * **Clustered Column / Histogram** phân bố số đơn hàng theo nhóm `Discount` (tạo Bins cho `Discount` hoặc `Sales`).
  * **Slicer** bên trái (`Order Year`, `Region`, `Category`, `Segment`).
* **Trang 2 – Xu hướng theo thời gian & Dự báo (SV 2):**
  * **Line Chart** (`DimDate[YearMonth]` theo `Total Sales` & `Total Profit`) + bật **Analytics → Forecast** (dự báo 6 tháng tới ngay trong Power BI!).
  * **Matrix** (`Year` × `Month Name`) bật Conditional Formatting làm Heatmap mùa vụ.
* **Trang 3 – Phân tích Khu vực & Bản đồ (SV 3):**
  * **Clustered Bar Chart** so sánh `Total Sales` & `Total Profit` theo `Region`.
  * **Filled Map (Choropleth)** đặt `State` vào Location (nhớ chỉnh Data Category của `State` thành **State or Province**), `Total Sales` vào Color saturation.
* **Trang 4 – Phân tích Sản phẩm & Chiết khấu (SV 4):**
  * **Bar Chart** lọc **Top N = 10** `Product Name` theo `Total Sales` (trong Filter pane chọn *Top N*).
  * **Treemap** phân cấp `Category → Sub-Category` theo `Total Sales` và tô màu theo `Profit Margin %`.
  * **Scatter Chart** (`Avg Discount %` vs `Total Profit` theo `Sub-Category`) để minh họa ngưỡng lỗ > 20%.

## Bước 5: Lưu và đẩy file `.pbix` lên GitHub
1. Chọn **File → Save as** → lưu thành `powerbi/Superstore_Dashboard.pbix`.
2. Đẩy lên GitHub:
   ```bash
   git add powerbi/Superstore_Dashboard.pbix
   git commit -m "Add Power BI Desktop dashboard (.pbix)"
   git push origin main
   ```

