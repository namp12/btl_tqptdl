"""Page 5: Trải nghiệm người dùng — Sidebar, Tabs/Expander, @st.cache_data & Gemini Flash Chatbot."""

from __future__ import annotations

import time

import pandas as pd
import plotly.express as px
import streamlit as st

from components.ai_chatbot import render_ai_chatbot
from components.sidebar import init_page, render_global_sidebar
from data.analytics import (
    detect_loss_anomalies,
    pivot_region_category,
    pivot_year_segment,
    simulate_discount_what_if,
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
tab_ai, tab_sim, tab_lookup, tab_disc, tab_pivot, tab_data = st.tabs(
    [
        "🤖 Trợ lý AI Phân tích B2B (Gemini Flash)",
        "🎯 What-If Simulator & Cảnh báo Lỗ",
        "🔎 Tra cứu 360° (Đơn / Khách / SP)",
        "📉 Tác động Chiết khấu & Lợi nhuận",
        "🧮 Pivot Table & GroupBy",
        "🗂️ Dữ liệu sạch & Xuất Báo cáo",
    ]
)

with tab_ai:
    render_ai_chatbot(df_filtered, location="main")

with tab_sim:
    st.subheader("🎯 Mô phỏng Kịch bản Kinh doanh (What-If Simulator)")
    st.caption(
        "Giả lập tác động tài chính nếu đặt trần chiết khấu tối đa và điều chỉnh giá nhóm hàng lỗ "
        "(giả định sản lượng giữ nguyên, giá vốn suy ra từ Sales - Profit)."
    )
    s1, s2 = st.columns(2)
    with s1:
        cap_pct = st.slider("Đặt trần chiết khấu tối đa (%)", min_value=0, max_value=50, value=20, step=5)
    with s2:
        uplift_pct = st.slider(
            "Điều chỉnh giá nhóm lỗ Tables/Bookcases/Supplies (%)",
            min_value=-10,
            max_value=25,
            value=5,
            step=1,
        )

    sim_res = simulate_discount_what_if(
        df_filtered,
        max_discount_cap=cap_pct / 100.0,
        loss_subcat_uplift_pct=float(uplift_pct),
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        "Lợi nhuận mô phỏng",
        format_usd(sim_res["sim_profit"]),
        delta=f"+{format_usd(sim_res['profit_gain'])}" if sim_res["profit_gain"] >= 0 else format_usd(sim_res["profit_gain"]),
    )
    m2.metric(
        "Biên lợi nhuận mới",
        f"{sim_res['sim_margin_pct']:.2f}%",
        delta=f"{sim_res['sim_margin_pct'] - sim_res['actual_margin_pct']:+.2f}%",
    )
    m3.metric("Doanh thu mô phỏng", format_usd(sim_res["sim_sales"]))
    m4.metric(
        "Giao dịch bị lỗ còn lại",
        format_int(sim_res["sim_loss_rows"]),
        delta=f"{sim_res['sim_loss_rows'] - sim_res['actual_loss_rows']:,} dòng",
        delta_color="inverse",
    )

    compare_df = pd.DataFrame(
        {
            "Kịch bản": ["Thực tế hiện tại", "Thực tế hiện tại", "Mô phỏng What-If", "Mô phỏng What-If"],
            "Chỉ số": ["Doanh thu", "Lợi nhuận", "Doanh thu", "Lợi nhuận"],
            "Giá trị (USD)": [
                sim_res["actual_sales"],
                sim_res["actual_profit"],
                sim_res["sim_sales"],
                sim_res["sim_profit"],
            ],
        }
    )
    fig_sim = px.bar(
        compare_df,
        x="Chỉ số",
        y="Giá trị (USD)",
        color="Kịch bản",
        barmode="group",
        text_auto=".2s",
        title="So sánh Doanh thu & Lợi nhuận: Thực tế vs. Kịch bản What-If",
    )
    st.plotly_chart(fig_sim, use_container_width=True)

    st.divider()
    st.subheader("🚨 Trung tâm Cảnh báo Đơn hàng Thua lỗ Nghiêm trọng")
    loss_thresh = st.slider(
        "Ngưỡng cảnh báo lỗ tối thiểu (Profit ≤ USD)",
        min_value=-1000,
        max_value=-20,
        value=-150,
        step=10,
    )
    anomalies_df = detect_loss_anomalies(df_filtered, profit_threshold=float(loss_thresh))
    if anomalies_df.empty:
        st.success("Không có đơn hàng nào lỗ vượt ngưỡng cảnh báo trong bộ lọc hiện tại.")
    else:
        st.warning(f"Phát hiện **{len(anomalies_df):,}** giao dịch có lợi nhuận ≤ {format_usd(loss_thresh)}.")
        st.dataframe(
            anomalies_df.style.format({"Sales": "${:,.2f}", "Profit": "${:,.2f}", "Discount": "{:.0%}"}),
            use_container_width=True,
            hide_index=True,
        )

with tab_lookup:
    st.subheader("🔎 Tra cứu Hồ sơ 360° (Đơn hàng, Khách hàng & Sản phẩm)")
    q1, q2 = st.columns([1.2, 2.8])
    with q1:
        lookup_type = st.selectbox(
            "Tìm kiếm theo trường",
            options=["Customer Name", "Order ID", "Product Name", "City", "State"],
        )
    with q2:
        search_text = st.text_input(
            "Nhập từ khóa tra cứu",
            placeholder="Ví dụ: Sean Miller, CA-2016-152156, Canon, Texas...",
        ).strip()

    if not search_text:
        st.info("Nhập từ khóa để tra cứu nhanh chi tiết giao dịch và tổng hợp KPI tương ứng.")
    else:
        matched = df_filtered[
            df_filtered[lookup_type].astype(str).str.contains(search_text, case=False, na=False)
        ]
        if matched.empty:
            st.warning(f"Không tìm thấy kết quả nào cho `{search_text}` trong `{lookup_type}`.")
        else:
            lk1, lk2, lk3, lk4 = st.columns(4)
            lk1.metric("Số dòng khớp", format_int(len(matched)))
            lk2.metric("Số đơn hàng", format_int(matched["Order ID"].nunique()))
            lk3.metric("Tổng doanh thu", format_usd(matched["Sales"].sum()))
            lk4.metric("Tổng lợi nhuận", format_usd(matched["Profit"].sum()))

            display_cols = [
                "Order ID",
                "Order Date",
                "Customer Name",
                "State",
                "Category",
                "Sub-Category",
                "Product Name",
                "Sales",
                "Quantity",
                "Discount",
                "Profit",
            ]
            st.dataframe(
                matched[display_cols].style.format(
                    {"Sales": "${:,.2f}", "Profit": "${:,.2f}", "Discount": "{:.0%}"}
                ),
                use_container_width=True,
                hide_index=True,
            )

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
    st.subheader("Xem trước dữ liệu sau khi làm sạch và xuất báo cáo nhanh")
    st.dataframe(df_filtered.head(100), use_container_width=True, hide_index=True)

    dl1, dl2 = st.columns(2)
    with dl1:
        csv_bytes = df_filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇️ Tải xuống dữ liệu đã lọc (CSV)",
            data=csv_bytes,
            file_name="superstore_cleaned_filtered.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dl2:
        tot_sales = float(df_filtered["Sales"].sum())
        tot_profit = float(df_filtered["Profit"].sum())
        margin_pct = (tot_profit / tot_sales * 100.0) if tot_sales else 0.0
        top_cat = df_filtered.groupby("Category")["Profit"].sum().idxmax()
        worst_subcat = df_filtered.groupby("Sub-Category")["Profit"].sum().idxmin()
        summary_md = (
            f"# BÁO CÁO TÓM TẮT ĐIỀU HÀNH SUPERSTORE\n\n"
            f"- **Phạm vi dữ liệu:** {df_filtered['Order Date'].min().strftime('%Y-%m-%d')} → "
            f"{df_filtered['Order Date'].max().strftime('%Y-%m-%d')} ({len(df_filtered):,} dòng)\n"
            f"- **Tổng doanh thu:** {format_usd(tot_sales)}\n"
            f"- **Tổng lợi nhuận:** {format_usd(tot_profit)} (Biên lợi nhuận: {margin_pct:.2f}%)\n"
            f"- **Tổng số đơn hàng:** {format_int(df_filtered['Order ID'].nunique())}\n"
            f"- **Ngành hàng sinh lời cao nhất:** {top_cat}\n"
            f"- **Nhóm sản phẩm cần tối ưu nhất:** {worst_subcat}\n"
        ).encode("utf-8")
        st.download_button(
            label="📝 Tải Báo cáo Tóm tắt Điều hành (.md)",
            data=summary_md,
            file_name="executive_summary_superstore.md",
            mime="text/markdown",
            use_container_width=True,
        )

with st.expander("🛠️ Chi tiết Kiến trúc Kỹ thuật: Cache, Session State & Chất lượng Dữ liệu"):
    st.markdown(
        f"""
        - **Clean Architecture:** Tách biệt hoàn toàn thành 4 tầng `data/`, `components/`, `pages/`, `utils/`.
        - **Đồng bộ `st.session_state`:** Lưu trữ các bộ lọc toàn cục (`ss_date_range`, `ss_regions`, `ss_categories`, `ss_segments`, `ss_cap_outliers`) giúp giữ nguyên bộ lọc khi chuyển giữa Page 1–5.
        - **Tối ưu hiệu năng (`@st.cache_data`):** Dữ liệu CSV ({audit['rows']:,} dòng × {audit['columns']} cột, đã loại {audit['business_duplicates']} trùng lặp) chỉ nạp vào RAM một lần duy nhất.
        """
    )
