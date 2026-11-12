"""Page 5: Trải nghiệm người dùng — Sidebar, Tabs/Expander, @st.cache_data & Gemini Flash Chatbot."""

from __future__ import annotations

import time

import pandas as pd
import plotly.express as px
import streamlit as st

from components.ai_chatbot import render_ai_chatbot
from components.sidebar import init_page, render_global_sidebar
from data.analytics import (
    pivot_region_category,
    pivot_year_segment,
    summarize_by_time,
)
from utils.formatters import format_int, format_usd

init_page("Page 5 - UX, Cache & AI Chatbot", icon="✨")

# Đo thời gian nạp từ RAM nhờ @st.cache_data
start_time = time.perf_counter()
df_clean, audit, df_sidebar = render_global_sidebar()
load_elapsed_ms = (time.perf_counter() - start_time) * 1000.0

# Quy hoạch thêm các bộ lọc nâng cao vào Sidebar
with st.sidebar:
    st.subheader("🔍 Bộ lọc chuyên sâu (Page 5)")
    ship_modes = sorted(df_clean["Ship Mode"].unique().tolist())
    selected_ship_modes = st.multiselect(
        "Hình thức giao hàng (Ship Mode)",
        options=ship_modes,
        default=ship_modes,
    )
    max_discount = st.slider(
        "Chiết khấu tối đa (Discount ≤)",
        min_value=0.0,
        max_value=0.8,
        value=0.8,
        step=0.05,
    )

df_filtered = df_sidebar[
    (df_sidebar["Ship Mode"].isin(selected_ship_modes))
    & (df_sidebar["Discount"] <= max_discount)
]


@st.cache_data(show_spinner=False)
def build_cached_pivots(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cache kết quả Pivot Table để phản hồi real-time khi tương tác Dashboard."""
    return pivot_region_category(data), pivot_year_segment(data)


st.title("✨ Page 5: Trải nghiệm người dùng, Tối ưu Cache & Trợ lý AI")
st.caption(
    "Toàn bộ bộ lọc được quy hoạch tại Sidebar (đồng bộ `st.session_state`), "
    "phân tầng nội dung bằng `Tabs`/`Expander`, tăng tốc với `@st.cache_data` và tích hợp **Gemini 3.8 Flash**."
)

if df_filtered.empty:
    st.warning("Không có bản ghi nào khớp với các tiêu chí lọc trong Sidebar.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("⚡ Thời gian nạp Cache", f"{load_elapsed_ms:.2f} ms")
c2.metric("📄 Bản ghi đang lọc", f"{format_int(len(df_filtered))} / {format_int(len(df_clean))}")
c3.metric("💰 Doanh thu lọc được", format_usd(df_filtered["Sales"].sum()))
c4.metric("📈 Lợi nhuận lọc được", format_usd(df_filtered["Profit"].sum()))

# Tổ chức nội dung bằng Tabs
tab_ai, tab_disc, tab_pivot, tab_data = st.tabs(
    [
        "🤖 Trợ lý AI Phân tích B2B (Gemini Flash)",
        "📉 Tác động Chiết khấu & Lợi nhuận",
        "🧮 Pivot Table & GroupBy",
        "🗂️ Dữ liệu sạch & Tải CSV",
    ]
)

with tab_ai:
    render_ai_chatbot(df_filtered, location="main")

with tab_disc:
    st.subheader("Mối quan hệ giữa Chiết khấu (Discount) và Lợi nhuận (Profit)")
    fig_scatter = px.scatter(
        df_filtered,
        x="Discount",
        y="Profit",
        color="Category",
        size="Sales",
        hover_data=["State", "Sub-Category", "Region", "Sales", "Quantity"],
        title="Biểu đồ phân tán: Chiết khấu vs. Lợi nhuận theo Ngành hàng",
        labels={"Discount": "Tỷ lệ chiết khấu", "Profit": "Lợi nhuận (USD)"},
    )
    fig_scatter.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Điểm hòa vốn (0 USD)")
    st.plotly_chart(fig_scatter, use_container_width=True)

    with st.expander("💡 Giải thích Insight về chính sách chiết khấu"):
        loss_count = int((df_filtered["Profit"] < 0).sum())
        loss_pct = (loss_count / len(df_filtered) * 100.0) if len(df_filtered) else 0.0
        st.markdown(
            f"""
            - Tập dữ liệu đang lọc có **{format_int(loss_count)}** giao dịch lỗ ({loss_pct:.2f}%).
            - Khi chiết khấu vượt quá **20%**, phần lớn giao dịch rơi vào vùng lợi nhuận âm.
            """
        )

with tab_pivot:
    st.subheader("Tổng hợp đa chiều với Pivot Table (đã được @st.cache_data)")
    pivot_reg_cat, pivot_yr_seg = build_cached_pivots(df_filtered)

    with st.expander("1️⃣ Pivot Table: Doanh thu theo Khu vực (Region) × Danh mục (Category)", expanded=True):
        st.dataframe(pivot_reg_cat.style.format("${:,.2f}"), use_container_width=True)

    with st.expander("2️⃣ Pivot Table: Doanh thu & Số đơn hàng theo Năm × Phân khúc (Segment)", expanded=True):
        st.dataframe(pivot_yr_seg.round(2), use_container_width=True)

    with st.expander("3️⃣ GroupBy: Tổng hợp doanh thu và đơn hàng theo Năm"):
        yr_summary = summarize_by_time(df_filtered, freq="Y")
        st.dataframe(
            yr_summary.style.format(
                {
                    "Total_Sales": "${:,.2f}",
                    "Total_Profit": "${:,.2f}",
                    "Order_Count": "{:,}",
                    "Total_Quantity": "{:,}",
                    "Profit_Margin_Pct": "{:.2f}%",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

with tab_data:
    st.subheader("Xem trước dữ liệu sau khi làm sạch và chuẩn hóa")
    st.dataframe(df_filtered.head(100), use_container_width=True, hide_index=True)

    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="⬇️ Tải xuống dữ liệu đã lọc (CSV)",
        data=csv_bytes,
        file_name="superstore_cleaned_filtered.csv",
        mime="text/csv",
    )

with st.expander("🛠️ Chi tiết Kiến trúc Kỹ thuật: Cache, Session State & Chất lượng Dữ liệu"):
    st.markdown(
        f"""
        - **Clean Architecture:** Tách biệt hoàn toàn thành 4 tầng `data/`, `components/`, `pages/`, `utils/`.
        - **Đồng bộ `st.session_state`:** Lưu trữ các bộ lọc toàn cục (`ss_date_range`, `ss_regions`, `ss_categories`, `ss_segments`, `ss_cap_outliers`) giúp giữ nguyên bộ lọc khi chuyển giữa Page 1–5.
        - **Tối ưu hiệu năng (`@st.cache_data`):** Dữ liệu CSV ({audit['rows']:,} dòng × {audit['columns']} cột, đã loại {audit['business_duplicates']} trùng lặp) chỉ nạp vào RAM một lần duy nhất.
        """
    )
