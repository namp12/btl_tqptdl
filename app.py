"""Trang chủ hệ thống Dashboard Phân tích Dữ liệu Bán lẻ Superstore (Clean Architecture)."""

from __future__ import annotations

import streamlit as st

from components.sidebar import init_page, render_global_sidebar
from utils.formatters import format_int, format_usd

init_page("Trang chủ", icon="🏬")
df_clean, audit, df_filtered = render_global_sidebar()

st.title("🏬 Hệ thống Phân tích Kinh doanh Superstore (BI & AI)")
st.markdown(
    """
    Ứng dụng Business Intelligence (BI) kiến trúc sạch (`data/`, `components/`, `pages/`, `utils/`),
    tích hợp **Dự báo chuỗi thời gian (Prophet/ARIMA)**, **Phân khúc khách hàng RFM**, **Luật kết hợp Apriori**,
    **Bản đồ địa lý Hoa Kỳ**, **Biểu đồ phân cấp Sunburst** và **Trợ lý AI Gemini 3.8 Flash**.
    """
)

st.divider()
st.subheader("📌 Tổng quan dữ liệu hiện tại (Đồng bộ `st.session_state`)")
col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Số bản ghi đang chọn",
    f"{format_int(len(df_filtered))} / {format_int(len(df_clean))}",
    delta=f"-{audit['business_duplicates']} trùng lặp gốc",
)
col2.metric("Tổng doanh thu", format_usd(df_filtered["Sales"].sum()))
col3.metric("Tổng đơn hàng", format_int(df_filtered["Order ID"].nunique()))
col4.metric("Tổng lợi nhuận", format_usd(df_filtered["Profit"].sum()))

st.divider()
st.subheader("🧭 Kiến trúc 5 trang Dashboard")

pages_info = [
    ("Page 1 — Tổng quan & RFM", "`st.metric` KPI cốt lõi + **Phân khúc khách hàng RFM** (VIP, Nguy cơ rời bỏ, Khách hàng mới)."),
    ("Page 2 — Xu hướng & Dự báo", "Plotly Line chart + bộ lọc động + **Dự báo 3–6 tháng (Prophet / ARIMA)** đường nét đứt."),
    ("Page 3 — Khu vực & Bản đồ Mỹ", "Plotly Bar chart + `st.multiselect` + **Bản đồ nhiệt Choropleth Hoa Kỳ** theo từng tiểu bang."),
    ("Page 4 — Sản phẩm & Giỏ hàng", "Top N sản phẩm + **Biểu đồ Sunburst/Treemap khoan sâu** + **Market Basket (Apriori)**."),
    ("Page 5 — UX, Cache & AI Chatbot", "Sidebar đồng bộ `st.session_state`, `Tabs`/`Expander`, `@st.cache_data` và **Gemini 3.8 Flash B2B Chatbot**."),
]

for title, desc in pages_info:
    st.markdown(f"- **{title}:** {desc}")

st.info("👉 Thử thay đổi bộ lọc ở Sidebar bên trái rồi chuyển sang các trang Page 1–5 để kiểm chứng đồng bộ State.")
