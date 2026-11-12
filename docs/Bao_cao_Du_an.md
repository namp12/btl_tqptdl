# BÁO CÁO BÀI TẬP LỚN: PHÂN TÍCH VÀ TRỰC QUAN HÓA DỮ LIỆU BÁN LẺ SUPERSTORE

---

## PHẦN 1 – MÔ TẢ DỮ LIỆU (10%)

### 1.1. Nguồn dữ liệu
* **Nguồn thu thập:** Bộ dữ liệu **Superstore Sales Dataset** (`Sample - Superstore.csv`), khai thác từ nền tảng dữ liệu mở **Kaggle**.
* **Bối cảnh bài toán:** Dữ liệu ghi nhận các giao dịch bán lẻ của chuỗi siêu thị Superstore tại Hoa Kỳ giai đoạn 2014–2017, phục vụ phân tích doanh thu, lợi nhuận, hành vi mua hàng theo khu vực, phân khúc khách hàng và danh mục sản phẩm.

### 1.2. Kích thước dữ liệu
* **Số dòng:** `9.994` dòng bản ghi gốc (còn `9.993` dòng sau khi loại 1 bản ghi trùng lặp nghiệp vụ).
* **Số cột:** `21` cột thuộc tính.

### 1.3. Ý nghĩa các biến (21 cột)
* **Nhóm thông tin đơn hàng:**
  * `Row ID`: Số thứ tự định danh dòng bản ghi.
  * `Order ID`: Mã định danh đơn hàng (`5.009` đơn hàng).
  * `Order Date`: Ngày đặt hàng.
* **Nhóm thông tin khách hàng & Giao hàng:**
  * `Customer ID`: Mã định danh khách hàng (`793` khách hàng).
  * `Customer Name`: Họ và tên khách hàng.
  * `Segment`: Phân khúc khách hàng (`Consumer`, `Corporate`, `Home Office`).
  * `Ship Date`: Ngày giao hàng.
  * `Ship Mode`: Hình thức vận chuyển (`Standard Class`, `Second Class`, `First Class`, `Same Day`).
  * `Country`: Quốc gia (`United States`).
  * `City`: Thành phố (`531` thành phố).
  * `State`: Tiểu bang (`49` tiểu bang).
  * `Postal Code`: Mã bưu chính nơi nhận hàng.
  * `Region`: Khu vực địa lý (`West`, `East`, `Central`, `South`).
* **Nhóm thông tin sản phẩm:**
  * `Product ID`: Mã định danh sản phẩm (`1.862` mã sản phẩm).
  * `Category`: Ngành hàng chính (`Technology`, `Furniture`, `Office Supplies`).
  * `Sub-Category`: Nhóm sản phẩm chi tiết (`17` nhóm).
  * `Product Name`: Tên chi tiết sản phẩm.
* **Nhóm chỉ số kinh doanh:**
  * `Sales`: Doanh thu thuần (USD).
  * `Quantity`: Số lượng sản phẩm bán ra.
  * `Discount`: Tỷ lệ chiết khấu (`0.00` đến `0.80`).
  * `Profit`: Lợi nhuận thực tế thu được (USD; âm là thua lỗ).

### 1.4. Kiểu dữ liệu
* **`object` / chuỗi ký tự (15 cột):** `Order ID`, `Order Date`, `Ship Date`, `Ship Mode`, `Customer ID`, `Customer Name`, `Segment`, `Country`, `City`, `State`, `Region`, `Product ID`, `Category`, `Sub-Category`, `Product Name`.
* **`int64` / số nguyên (3 cột):** `Row ID`, `Postal Code`, `Quantity`.
* **`float64` / số thực (3 cột):** `Sales`, `Discount`, `Profit`.

---

## PHẦN 2 – KHÁM PHÁ VÀ XỬ LÝ DỮ LIỆU (EDA) (25%)

Quy trình EDA được thực hiện bằng Python/Pandas trong [`data/loader.py`](../data/loader.py), [`data/analytics.py`](../data/analytics.py), script [`eda_superstore.py`](../eda_superstore.py) và notebook [`notebooks/01_EDA_Superstore.ipynb`](../notebooks/01_EDA_Superstore.ipynb).

### 2.1. Kiểm tra dữ liệu thiếu, trùng lặp và ngoại lệ
* **Dữ liệu thiếu (Missing Values):** Kiểm tra bằng `df.isna().sum()` cho kết quả **0 giá trị thiếu** trên toàn bộ 21 cột.
* **Dữ liệu trùng lặp:** Phát hiện `1` bản ghi trùng lặp nghiệp vụ khi loại trừ `Row ID` (tại `Row ID = 3407`) và đã loại bỏ để giữ `9.993` dòng hợp lệ.
* **Chuẩn hóa kiểu dữ liệu:** Chuyển `Order Date` và `Ship Date` từ `object` sang `datetime64[ns]`; chuẩn hóa `Postal Code` sang chuỗi 5 ký tự; kiểm tra `Ship Date < Order Date` (`0` lỗi).
* **Kiểm tra & xử lý ngoại lệ (IQR 1.5×):** Phát hiện `1.167` điểm ngoại lệ ở `Sales` và `1.881` điểm ở `Profit`. Hệ thống gắn cờ ngoại lệ (`Is_Sales_Outlier`, `Is_Profit_Outlier`) để bảo toàn các đơn hàng B2B thực tế, đồng thời cung cấp tùy chọn **IQR Winsorize** trên Sidebar.

### 2.2. Thống kê mô tả
Tổng doanh thu đạt `2,297,200.86 USD`, tổng lợi nhuận `286,397.02 USD` (biên lợi nhuận `12.47%`), tổng số lượng `37,873` đơn vị:
* `Sales`: Mean `229.86 USD`, Median `54.49 USD`, Min `0.44 USD`, Max `22,638.48 USD`.
* `Profit`: Mean `28.66 USD`, Median `8.67 USD`, Min `-6,599.98 USD`, Max `8,399.98 USD`.
* `Discount`: Mean `0.1562`, Median `0.20`, Max `0.80`.
* `Quantity`: Mean `3.79`, Median `3.00`, Min `1`, Max `14`.

### 2.3. Lọc dữ liệu theo điều kiện
* Lọc các giao dịch thua lỗ (`Profit < 0`): ghi nhận **1.871 dòng** (`18.72%`).
* Lọc các giao dịch chiết khấu sâu (`Discount > 0.2`): có `1.393` dòng, trong đó tỷ lệ thua lỗ lên tới **96.77%** (lợi nhuận trung bình `-97.18 USD`).
* Xây dựng hàm lọc đa điều kiện [`filter_dataframe`](../data/loader.py#L121-L137) theo khoảng thời gian, `Region`, `Category` và `Segment`.

### 2.4. Tổng hợp bằng GroupBy và Pivot Table
* **GroupBy theo Năm:** Doanh thu tăng từ `484,247.50 USD` (2014) lên `470,532.51 USD` (2015), `609,205.60 USD` (2016) và `733,215.26 USD` (2017).
* **GroupBy theo Khu vực:** `West` (`725,457.82 USD`, biên `14.94%`) và `East` (`678,781.24 USD`, biên `13.48%`) dẫn đầu; `Central` có biên lợi nhuận thấp nhất (`7.92%`).
* **GroupBy theo Danh mục:** `Technology` (`145,454.95 USD` lợi nhuận, biên `17.40%`) và `Office Supplies` (`122,490.80 USD`, biên `17.04%`) hiệu quả cao; `Furniture` chỉ đạt biên `2.49%` do `Tables` lỗ `-17,725.48 USD` và `Bookcases` lỗ `-3,472.56 USD`.
* **Pivot Table:** Tạo bảng chéo `Region × Category` (doanh thu) và `Order_Year × Segment` (doanh thu & số đơn hàng).

---

## PHẦN 3 – TRỰC QUAN HÓA DỮ LIỆU (30%)

Hệ thống sử dụng **Plotly, Matplotlib và Seaborn**, đảm bảo đầy đủ 4 nhóm biểu đồ bắt buộc cùng các biểu đồ nâng cao:
1. **Biểu đồ so sánh (Bar / Line):** Biểu đồ cột so sánh doanh thu và lợi nhuận giữa các khu vực (`Page 3`), giữa các phân khúc (`Page 1`) và Top N sản phẩm (`Page 4`).
2. **Biểu đồ phân phối (Histogram / Boxplot):** Biểu đồ `Histogram` (kèm KDE/rug) thể hiện phân phối lệch phải của `Sales`, `Profit`, `Discount` và `Boxplot` thể hiện khoảng tứ phân vị cùng các điểm ngoại lệ theo `Category`/`Region`/`Segment` (`Page 1` & `01_EDA_Superstore.ipynb`).
3. **Biểu đồ xu hướng theo thời gian:** Biểu đồ đường (`px.line`) theo Tháng/Quý/Năm kèm mô hình **Dự báo doanh thu 3–6 tháng (Prophet / ARIMA)** vẽ đường nét đứt và dải tin cậy (`Page 2`).
4. **Biểu đồ tổng hợp (Grouped / Stacked):** Biểu đồ cột nhóm (`barmode="group"`) và cột chồng (`barmode="stack"`) đối chiếu doanh thu theo `Segment × Category` (`Page 1`) và doanh thu vs. lợi nhuận theo `Region` (`Page 3`).
5. **Trực quan hóa chuyên sâu:** **Bản đồ nhiệt Choropleth Hoa Kỳ** theo từng tiểu bang (`Page 3`) và **Biểu đồ phân cấp Sunburst / Treemap** cho phép click khoan sâu `Category → Sub-Category → Product Name` (`Page 4`).

---

## PHẦN 4 – DASHBOARD TƯƠNG TÁC STREAMLIT (25%)

### 4.1. Kiến trúc hệ thống & Đáp ứng yêu cầu Dashboard
* **Clean Architecture:** Chia 4 thư mục `data/`, `components/`, `pages/`, `utils/`.
* **Sidebar Filter (≥ 2 điều kiện) & Đồng bộ `st.session_state`:** Sidebar toàn cục tại [`components/sidebar.py`](../components/sidebar.py) gồm 5 điều kiện lọc (*Khoảng ngày đặt hàng*, *Khu vực*, *Danh mục*, *Phân khúc*, *Chặn trần ngoại lệ IQR*) được đồng bộ qua [`utils/session_state.py`](../utils/session_state.py) để giữ nguyên khi chuyển trang.
* **Tabs & Columns:** Mỗi trang sử dụng `st.columns` bố trí KPI/biểu đồ song song và `st.tabs`/`st.expander` phân tầng nội dung rõ ràng.
* **Tối ưu hiệu năng & AI:** Áp dụng `@st.cache_data` tại tầng nạp dữ liệu/tính toán và tích hợp **Chatbot B2B Gemini 3.8 Flash** (`google-genai`) trên Page 5.

### 4.2. Phân công nhóm 4 sinh viên (Mỗi thành viên phụ trách trang trực quan hóa cụ thể)
| Thành viên | Trang phụ trách | Nhiệm vụ trực quan hóa & Kỹ thuật |
| :--- | :--- | :--- |
| **Sinh viên 1** | `pages/1_Tong_Quan_Kinh_Doanh.py` | KPI (`st.metric`), **Biểu đồ tổng hợp (Grouped/Stacked Bar)**, **Biểu đồ phân phối (Histogram & Boxplot)** và **Phân khúc RFM**. |
| **Sinh viên 2** | `pages/2_Xu_Huong_Doanh_Thu.py` | **Biểu đồ xu hướng theo thời gian** (Plotly Line), bộ lọc động (`date_input`/`slider`) và **Dự báo Prophet / ARIMA** 3–6 tháng. |
| **Sinh viên 3** | `pages/3_Phan_Tich_Khu_Vuc.py` | **Biểu đồ so sánh khu vực (Bar chart)**, bộ lọc `multiselect`, Pivot Table và **Bản đồ Choropleth Hoa Kỳ**. |
| **Sinh viên 4** | `pages/4_Phan_Tich_San_Pham.py` & đồng hoàn thiện `pages/5_Trai_Nghiem_Nguoi_Dung.py` | Top N sản phẩm, **Sunburst / Treemap khoan sâu**, **Market Basket (Apriori)**; tích hợp Sidebar dùng chung, `@st.cache_data` và **Gemini AI Chatbot**. |

---

## PHẦN 5 – NHẬN XÉT & INSIGHT (10%)

### 5.1. Phát hiện chính từ dữ liệu
* **Chiết khấu trên 20% là nguyên nhân gây lỗ chính:** Giao dịch không chiết khấu đạt lợi nhuận TB `66.90 USD` (`0%` lỗ); giao dịch chiết khấu `> 20%` lỗ trung bình `-97.18 USD` với tỷ lệ lỗ **96.77%**.
* **Nghịch lý doanh thu – lợi nhuận ở `Furniture`:** Đứng thứ 2 về doanh thu (`741,999.80 USD`) nhưng biên lợi nhuận chỉ đạt `2.49%` do `Tables` (`-17,725.48 USD`) và `Bookcases` (`-3,472.56 USD`) kéo giảm.

### 5.2. So sánh & Xu hướng nổi bật
* Doanh thu tăng trưởng liên tục qua 4 năm (2014–2017) và đạt đỉnh mùa vụ vào Quý 4 hằng năm (tháng 11–12).
* Hai khu vực `West` và `East` tạo gần 70% tổng lợi nhuận; `Central` có biên lợi nhuận thấp nhất (`7.92%`).
* Phân khúc `Consumer` đóng góp doanh thu lớn nhất (`50.56%`), trong khi `Home Office` đạt biên lợi nhuận cao nhất (`14.03%`).

### 5.3. Gợi ý ra quyết định kinh doanh
1. **Thiết lập trần chiết khấu tối đa 20%:** Yêu cầu phê duyệt quản lý đối với mọi đơn hàng giảm giá trên 20% để ngăn chặn bán lỗ.
2. **Tái cấu trúc nhóm `Tables` và `Bookcases`:** Rà soát chi phí vận chuyển cồng kềnh, điều chỉnh giá hoặc bán kèm (cross-sell) theo gợi ý từ thuật toán **Apriori** với các mặt hàng biên lợi nhuận cao.
3. **Tối ưu thị trường `Central` (đặc biệt bang Texas):** Cắt giảm khuyến mãi sâu không hiệu quả tại khu vực Central để đưa biên lợi nhuận tiệm cận mức trung bình `12.47%`.
4. **Cá nhân hóa chăm sóc theo RFM:** Giữ chân nhóm *VIP* và kích hoạt sớm nhóm *Nguy cơ rời bỏ* bằng ưu đãi có điều kiện trên nhóm sản phẩm `Technology` (`Copiers`, `Phones`).
