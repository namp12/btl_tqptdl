"""Page 4: Phân tích sản phẩm — Top N, Sunburst/Treemap phân cấp & Market Basket (Apriori)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from components.sidebar import init_page, render_global_sidebar
from data.analytics import (
    run_market_basket_apriori,
    summarize_by_category,
    summarize_top_products,
)

init_page("Page 4 - Sản phẩm, Sunburst & Giỏ hàng", icon="🏆")
_, _, df_sidebar = render_global_sidebar()


@st.cache_data(show_spinner="Đang khai phá luật kết hợp Apriori...")
def cached_apriori(
    data: pd.DataFrame,
    item_col: str,
    min_support: float,
    min_confidence: float,
) -> pd.DataFrame:
    """Cache kết quả Market Basket Analysis để phản hồi mượt mà."""
    return run_market_basket_apriori(
        data,
        item_col=item_col,
        min_support=min_support,
        min_confidence=min_confidence,
    )


st.title("🏆 Page 4: Phân tích sản phẩm, Sunburst & Giỏ hàng (Apriori)")
st.caption(
    "Xếp hạng Top N sản phẩm, khoan sâu phân cấp Category → Sub-Category → Product bằng Sunburst "
    "và tìm sản phẩm mua kèm bằng thuật toán Apriori."
)

if df_sidebar.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc Sidebar hiện tại.")
    st.stop()

# Bộ lọc bổ sung theo Top N, Thời gian và Khu vực
min_dt = df_sidebar["Order Date"].min().date()
max_dt = df_sidebar["Order Date"].max().date()
all_regions = sorted(df_sidebar["Region"].unique().tolist())

c1, c2, c3 = st.columns([1.2, 1.8, 2])
with c1:
    top_n = st.slider("Số lượng Top N sản phẩm", min_value=5, max_value=25, value=10, step=1)
with c2:
    date_range = st.date_input(
        "Lọc thêm theo thời gian",
        value=(min_dt, max_dt),
        min_value=min_dt,
        max_value=max_dt,
    )
with c3:
    selected_regions = st.multiselect(
        "Lọc thêm theo khu vực",
        options=all_regions,
        default=all_regions,
    )

if not selected_regions:
    st.warning("Vui lòng chọn ít nhất một khu vực.")
    st.stop()

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_dt, end_dt = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_dt, end_dt = pd.Timestamp(min_dt), pd.Timestamp(max_dt)

df_filtered = df_sidebar[
    (df_sidebar["Order Date"] >= start_dt)
    & (df_sidebar["Order Date"] <= end_dt)
    & (df_sidebar["Region"].isin(selected_regions))
]

if df_filtered.empty:
    st.warning("Không có giao dịch nào thỏa mãn điều kiện lọc.")
    st.stop()

tab_top, tab_sunburst, tab_apriori = st.tabs(
    [
        f"🏅 Top {top_n} Sản phẩm & Sub-Category",
        "🌞 Biểu đồ phân cấp (Sunburst / Treemap)",
        "🛒 Phân tích Giỏ hàng (Market Basket - Apriori)",
    ]
)

with tab_top:
    top_products = summarize_top_products(df_filtered, top_n=top_n)
    top_sorted = top_products.sort_values("Total_Sales", ascending=True).copy()
    top_sorted["Short_Name"] = top_sorted["Product Name"].apply(
        lambda s: s if len(s) <= 44 else s[:41] + "..."
    )

    fig_top = px.bar(
        top_sorted,
        x="Total_Sales",
        y="Short_Name",
        color="Category",
        orientation="h",
        text_auto=".2s",
        hover_data={"Product Name": True, "Short_Name": False, "Total_Sales": ":,.2f", "Total_Profit": ":,.2f"},
        title=f"Top {top_n} sản phẩm có doanh thu cao nhất",
        labels={"Total_Sales": "Tổng doanh thu (USD)", "Short_Name": "Sản phẩm", "Category": "Ngành hàng"},
        height=max(420, top_n * 30),
    )
    st.plotly_chart(fig_top, use_container_width=True)

    subcat_df = summarize_by_category(df_filtered).sort_values("Total_Profit", ascending=True)
    fig_subcat = px.bar(
        subcat_df,
        x="Total_Profit",
        y="Sub-Category",
        color="Total_Profit",
        color_continuous_scale="RdYlGn",
        orientation="h",
        title="Hiệu suất Lợi nhuận theo Nhóm sản phẩm (Sub-Category)",
        labels={"Total_Profit": "Tổng lợi nhuận (USD)", "Sub-Category": "Nhóm sản phẩm"},
        height=500,
    )
    st.plotly_chart(fig_subcat, use_container_width=True)

with tab_sunburst:
    st.subheader("🌞 Khoan sâu phân cấp: Category → Sub-Category → Product Name")
    st.caption("Nhấp chuột vào từng lát cắt để phóng to (drill-down) vào nhóm sản phẩm chi tiết.")
    chart_style = st.radio(
        "Kiểu biểu đồ phân cấp",
        options=["Sunburst", "Treemap"],
        horizontal=True,
    )
    hierarchy_df = (
        df_filtered.groupby(["Category", "Sub-Category", "Product Name"], as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
    )
    hierarchy_df = hierarchy_df[hierarchy_df["Sales"] > 0]

    if chart_style == "Sunburst":
        fig_hier = px.sunburst(
            hierarchy_df,
            path=["Category", "Sub-Category", "Product Name"],
            values="Sales",
            color="Profit",
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0,
            title="Biểu đồ Sunburst Doanh thu (Kích thước) & Lợi nhuận (Màu sắc)",
            height=650,
        )
    else:
        fig_hier = px.treemap(
            hierarchy_df,
            path=["Category", "Sub-Category", "Product Name"],
            values="Sales",
            color="Profit",
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0,
            title="Biểu đồ Treemap Doanh thu (Kích thước) & Lợi nhuận (Màu sắc)",
            height=650,
        )
    st.plotly_chart(fig_hier, use_container_width=True)

with tab_apriori:
    st.subheader("🛒 Phân tích Giỏ hàng (Market Basket Analysis — Thuật toán Apriori)")
    st.caption("Tìm các nhóm/mặt hàng thường xuất hiện trong cùng một đơn hàng (`Order ID`) để đề xuất bán chéo (cross-sell).")

    a1, a2, a3 = st.columns(3)
    with a1:
        item_granularity = st.selectbox("Cấp độ phân tích giỏ hàng", options=["Sub-Category", "Category"])
    with a2:
        min_support = st.slider("Min Support (Tần suất tối thiểu)", 0.005, 0.10, 0.015, 0.005)
    with a3:
        min_confidence = st.slider("Min Confidence (Độ tin cậy tối thiểu)", 0.10, 0.80, 0.20, 0.05)

    rules_df = cached_apriori(df_filtered, item_granularity, min_support, min_confidence)
    if rules_df.empty:
        st.info("Không tìm thấy luật kết hợp nào thỏa mãn ngưỡng Support/Confidence. Hãy thử giảm ngưỡng lọc.")
    else:
        rules_plot = rules_df.head(12).copy()
        rules_plot["Rule"] = rules_plot["Antecedents"] + " → " + rules_plot["Consequents"]
        fig_rules = px.bar(
            rules_plot.sort_values("Lift", ascending=True),
            x="Lift",
            y="Rule",
            color="Confidence",
            orientation="h",
            hover_data=["Support", "Pair_Orders"],
            title="Top các cặp sản phẩm thường mua cùng nhau (Xếp theo Lift)",
            labels={"Lift": "Chỉ số Lift (> 1 là liên kết dương)", "Rule": "Luật bán chéo"},
            height=450,
        )
        st.plotly_chart(fig_rules, use_container_width=True)

        st.dataframe(
            rules_df.style.format({"Support": "{:.2%}", "Confidence": "{:.2%}", "Lift": "{:.2f}"}),
            use_container_width=True,
            hide_index=True,
        )
