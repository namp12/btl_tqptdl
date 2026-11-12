"""Page 1: Tổng quan kinh doanh (st.metric) & Phân khúc khách hàng RFM."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from components.sidebar import init_page, render_global_sidebar
from data.analytics import (
    compute_cohort_retention,
    compute_kmeans_clusters,
    compute_rfm_segments,
    summarize_by_category,
)
from utils.formatters import format_int, format_usd

init_page("Page 1 - Tổng quan & RFM", icon="📊")
_, _, df = render_global_sidebar()


@st.cache_data(show_spinner=False)
def cached_rfm(data: pd.DataFrame) -> pd.DataFrame:
    """Cache kết quả tính toán phân khúc khách hàng RFM."""
    return compute_rfm_segments(data)


@st.cache_data(show_spinner=False)
def cached_cohort(data: pd.DataFrame) -> pd.DataFrame:
    """Cache ma trận tỷ lệ giữ chân khách hàng theo Cohort."""
    return compute_cohort_retention(data)


@st.cache_data(show_spinner=False)
def cached_kmeans(data: pd.DataFrame, k: int) -> pd.DataFrame:
    """Cache kết quả phân cụm khách hàng K-Means."""
    return compute_kmeans_clusters(data, n_clusters=k)


st.title("📊 Page 1: Tổng quan kinh doanh & Phân khúc khách hàng (RFM)")
st.caption("Theo dõi các KPI cốt lõi bằng `st.metric` và phân loại nhóm khách hàng theo mô hình RFM.")

if df.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc hiện tại. Vui lòng điều chỉnh lại Sidebar.")
    st.stop()

# 1. KPI cốt lõi bằng st.metric
total_sales = float(df["Sales"].sum())
total_orders = int(df["Order ID"].nunique())
total_quantity = int(df["Quantity"].sum())
total_profit = float(df["Profit"].sum())
profit_margin = (total_profit / total_sales * 100.0) if total_sales else 0.0
avg_order_value = (total_sales / total_orders) if total_orders else 0.0

col1, col2, col3 = st.columns(3)
col1.metric("💰 Tổng doanh thu (Total Sales)", format_usd(total_sales), delta=f"AOV: {format_usd(avg_order_value)}")
col2.metric("🧾 Tổng số đơn hàng (Total Orders)", format_int(total_orders), delta=f"{format_int(df['Customer ID'].nunique())} khách hàng")
col3.metric("📦 Tổng số lượng sản phẩm (Quantity)", format_int(total_quantity), delta=f"Biên LN: {profit_margin:.2f}%")

col4, col5, col6 = st.columns(3)
col4.metric("📈 Tổng lợi nhuận (Total Profit)", format_usd(total_profit))
col5.metric("🏷️ Chiết khấu trung bình", f"{df['Discount'].mean() * 100:.2f}%")
col6.metric("🚚 Thời gian giao hàng TB", f"{df['Shipping_Days'].mean():.1f} ngày")

st.divider()

tab_overview, tab_dist, tab_rfm, tab_cohort, tab_kmeans = st.tabs(
    [
        "📊 Cơ cấu & Biểu đồ Tổng hợp (Grouped/Stacked)",
        "📉 Phân phối Dữ liệu (Histogram & Boxplot)",
        "🎯 Phân khúc Khách hàng (RFM Analysis)",
        "🔁 Cohort Giữ chân Khách hàng",
        "🤖 ML Phân cụm (K-Means 3D)",
    ]
)

with tab_overview:
    left, right = st.columns(2)
    with left:
        cat_df = df.groupby("Category", as_index=False).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        fig_cat = px.pie(
            cat_df,
            values="Sales",
            names="Category",
            hole=0.45,
            title="Tỷ trọng Doanh thu theo Ngành hàng",
        )
        fig_cat.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_cat, use_container_width=True)

    with right:
        bar_mode_choice = st.radio(
            "Kiểu biểu đồ tổng hợp (Category × Segment)",
            options=["Stacked (Chồng cột)", "Grouped (Nhóm cột)"],
            horizontal=True,
        )
        barmode_val = "stack" if "Stacked" in bar_mode_choice else "group"
        cat_seg_df = (
            df.groupby(["Segment", "Category"], as_index=False)
            .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        )
        fig_seg = px.bar(
            cat_seg_df,
            x="Segment",
            y="Sales",
            color="Category",
            barmode=barmode_val,
            text_auto=".2s",
            title=f"Biểu đồ tổng hợp Doanh thu theo Phân khúc & Ngành hàng ({barmode_val.title()})",
            labels={"Sales": "Doanh thu (USD)", "Segment": "Phân khúc", "Category": "Ngành hàng"},
        )
        st.plotly_chart(fig_seg, use_container_width=True)

    st.subheader("📋 Bảng tổng hợp theo Danh mục (GroupBy)")
    cat_summary = summarize_by_category(df)
    st.dataframe(
        cat_summary.style.format(
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

with tab_dist:
    st.subheader("📉 Phân tích phân phối và ngoại lệ (Histogram & Boxplot)")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        hist_var = st.selectbox(
            "Chọn biến định lượng (Histogram)",
            options=["Sales", "Profit", "Discount", "Quantity", "Shipping_Days"],
        )
        fig_hist = px.histogram(
            df,
            x=hist_var,
            nbins=40,
            color="Category",
            marginal="rug",
            title=f"Phân phối tần suất (Histogram) của biến {hist_var}",
            labels={hist_var: hist_var, "count": "Số giao dịch"},
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with d_col2:
        box_group = st.selectbox(
            "Phân nhóm theo (Boxplot)",
            options=["Category", "Region", "Segment", "Ship Mode"],
        )
        fig_box = px.box(
            df,
            x=box_group,
            y=hist_var,
            color=box_group,
            points="outliers",
            title=f"Phân phối và Ngoại lệ (Boxplot) của {hist_var} theo {box_group}",
            labels={box_group: box_group, hist_var: hist_var},
        )
        st.plotly_chart(fig_box, use_container_width=True)

with tab_rfm:
    st.subheader("🎯 Phân tích RFM (Recency - Frequency - Monetary)")
    rfm_df = cached_rfm(df)

    rfm_summary = (
        rfm_df.groupby("RFM_Segment", as_index=False)
        .agg(
            Customer_Count=("Customer ID", "count"),
            Avg_Recency_Days=("Recency", "mean"),
            Avg_Frequency=("Frequency", "mean"),
            Total_Monetary=("Monetary", "sum"),
            Avg_Monetary=("Monetary", "mean"),
        )
        .sort_values("Total_Monetary", ascending=False)
    )

    c_left, c_right = st.columns(2)
    with c_left:
        fig_rfm_bar = px.bar(
            rfm_summary,
            x="RFM_Segment",
            y="Customer_Count",
            color="Total_Monetary",
            text_auto=True,
            title="Số lượng khách hàng và Tổng chi tiêu theo Nhóm RFM",
            labels={"RFM_Segment": "Nhóm RFM", "Customer_Count": "Số khách hàng", "Total_Monetary": "Tổng chi tiêu ($)"},
        )
        st.plotly_chart(fig_rfm_bar, use_container_width=True)

    with c_right:
        fig_rfm_scatter = px.scatter(
            rfm_df,
            x="Recency",
            y="Monetary",
            size="Frequency",
            color="RFM_Segment",
            hover_data=["Customer Name", "Frequency", "Total_Profit"],
            title="Phân bố Khách hàng: Recency (ngày) vs. Monetary (USD)",
            labels={"Recency": "Số ngày từ lần mua cuối", "Monetary": "Tổng chi tiêu (USD)"},
        )
        st.plotly_chart(fig_rfm_scatter, use_container_width=True)

    selected_rfm = st.multiselect(
        "Lọc danh sách khách hàng theo nhãn RFM",
        options=rfm_summary["RFM_Segment"].tolist(),
        default=rfm_summary["RFM_Segment"].tolist(),
    )
    rfm_view = rfm_df[rfm_df["RFM_Segment"].isin(selected_rfm)]
    st.dataframe(
        rfm_view[
            ["Customer ID", "Customer Name", "RFM_Segment", "Recency", "Frequency", "Monetary", "Total_Profit", "R_Score", "F_Score", "M_Score"]
        ].style.format({"Monetary": "${:,.2f}", "Total_Profit": "${:,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )

with tab_cohort:
    st.subheader("🔁 Ma trận giữ chân khách hàng theo Năm gia nhập (Cohort Retention %)")
    st.caption("Theo dõi tỷ lệ khách hàng quay lại mua sắm qua từng năm kể từ lần mua đầu tiên.")
    cohort_matrix = cached_cohort(df)
    if cohort_matrix.empty:
        st.info("Chưa đủ dữ liệu đa năm trong bộ lọc hiện tại để lập ma trận Cohort.")
    else:
        fig_cohort = px.imshow(
            cohort_matrix,
            text_auto=".1f",
            color_continuous_scale="YlGnBu",
            aspect="auto",
            title="Tỷ lệ giữ chân khách hàng (%) theo Cohort năm",
            labels={"x": "Số năm sau lần mua đầu", "y": "Nhóm Cohort", "color": "Tỷ lệ (%)"},
        )
        st.plotly_chart(fig_cohort, use_container_width=True)
        st.dataframe(cohort_matrix.style.format("{:.1f}%"), use_container_width=True)

with tab_kmeans:
    st.subheader("🤖 Phân cụm khách hàng tự động bằng K-Means (Machine Learning)")
    st.caption("Áp dụng K-Means trên không gian 3 chiều (Recency, log-Frequency, log-Monetary) đã chuẩn hóa Z-score.")
    k_val = st.slider("Chọn số cụm khách hàng (k)", min_value=3, max_value=6, value=4, step=1)
    km_df = cached_kmeans(df, k_val)

    fig_3d = px.scatter_3d(
        km_df,
        x="Recency",
        y="Frequency",
        z="Monetary",
        color="Cluster_Label",
        hover_data=["Customer Name", "RFM_Segment", "Total_Profit"],
        title=f"Biểu đồ 3D K-Means Clustering (k = {k_val})",
        labels={"Recency": "Recency (ngày)", "Frequency": "Tần suất (đơn)", "Monetary": "Chi tiêu (USD)"},
        height=560,
    )
    st.plotly_chart(fig_3d, use_container_width=True)

    cluster_profile = (
        km_df.groupby("Cluster_Label", as_index=False)
        .agg(
            So_Khach_Hang=("Customer ID", "count"),
            Recency_TB=("Recency", "mean"),
            Frequency_TB=("Frequency", "mean"),
            Monetary_TB=("Monetary", "mean"),
            Tong_Loi_Nhuan=("Total_Profit", "sum"),
        )
        .sort_values("Monetary_TB", ascending=False)
    )
    st.dataframe(
        cluster_profile.style.format(
            {
                "Recency_TB": "{:.1f} ngày",
                "Frequency_TB": "{:.1f} đơn",
                "Monetary_TB": "${:,.2f}",
                "Tong_Loi_Nhuan": "${:,.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
