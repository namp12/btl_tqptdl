"""Page 3: Phân tích khu vực — Bar chart đa vùng, multiselect và Bản đồ Choropleth Hoa Kỳ."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from components.sidebar import init_page, render_global_sidebar
from data.analytics import (
    pivot_region_category,
    summarize_by_region,
    summarize_by_state,
)

init_page("Page 3 - Khu vực & Bản đồ Mỹ", icon="🗺️")
_, _, df_sidebar = render_global_sidebar()

st.title("🗺️ Page 3: Phân tích khu vực & Bản đồ địa lý Hoa Kỳ")
st.caption("So sánh doanh thu theo vùng bằng biểu đồ cột (`multiselect`) và bản đồ nhiệt Choropleth theo từng tiểu bang.")

if df_sidebar.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc Sidebar hiện tại.")
    st.stop()

# Bộ lọc bắt buộc: st.multiselect chọn nhiều khu vực cùng lúc
available_regions = sorted(df_sidebar["Region"].unique().tolist())
selected_regions = st.multiselect(
    "Chọn các khu vực muốn so sánh (Region - Multiselect)",
    options=available_regions,
    default=available_regions,
)

if not selected_regions:
    st.warning("Vui lòng chọn ít nhất một khu vực để hiển thị.")
    st.stop()

df_filtered = df_sidebar[df_sidebar["Region"].isin(selected_regions)]
region_summary = summarize_by_region(df_filtered)
state_summary = summarize_by_state(df_filtered)

# 1. Biểu đồ cột so sánh giữa các vùng
col_left, col_right = st.columns(2)
with col_left:
    fig_region_bar = px.bar(
        region_summary,
        x="Region",
        y="Total_Sales",
        color="Region",
        text_auto=".2s",
        title="So sánh Tổng doanh thu theo Khu vực (Bar Chart)",
        labels={"Region": "Khu vực", "Total_Sales": "Tổng doanh thu (USD)"},
    )
    fig_region_bar.update_layout(showlegend=False)
    st.plotly_chart(fig_region_bar, use_container_width=True)

with col_right:
    fig_profit_bar = px.bar(
        region_summary,
        x="Region",
        y=["Total_Sales", "Total_Profit"],
        barmode="group",
        title="Đối chiếu Doanh thu và Lợi nhuận theo Khu vực",
        labels={"Region": "Khu vực", "value": "Giá trị (USD)", "variable": "Chỉ số"},
    )
    st.plotly_chart(fig_profit_bar, use_container_width=True)

st.divider()

# 2. Bản đồ địa lý Hoa Kỳ (Choropleth Map)
st.subheader("🇺🇸 Bản đồ nhiệt Doanh thu & Lợi nhuận theo Tiểu bang (Choropleth Map)")
map_metric_label = st.radio(
    "Chọn chỉ số hiển thị trên bản đồ",
    options=["Tổng doanh thu (Total_Sales)", "Tổng lợi nhuận (Total_Profit)", "Biên lợi nhuận (%)"],
    horizontal=True,
)
metric_col = {
    "Tổng doanh thu (Total_Sales)": "Total_Sales",
    "Tổng lợi nhuận (Total_Profit)": "Total_Profit",
    "Biên lợi nhuận (%)": "Profit_Margin_Pct",
}[map_metric_label]

color_scale = "Blues" if metric_col == "Total_Sales" else "RdYlGn"

fig_map = px.choropleth(
    state_summary.dropna(subset=["State_Code"]),
    locations="State_Code",
    locationmode="USA-states",
    color=metric_col,
    scope="usa",
    hover_name="State",
    hover_data={
        "State_Code": True,
        "Region": True,
        "Total_Sales": ":,.2f",
        "Total_Profit": ":,.2f",
        "Profit_Margin_Pct": ":.2f",
        "Order_Count": ":,",
    },
    color_continuous_scale=color_scale,
    title=f"Bản đồ phân bố {map_metric_label} tại Hoa Kỳ (Zoom & Di chuột để xem chi tiết)",
)
fig_map.update_layout(
    geo=dict(lakecolor="rgb(255, 255, 255)"),
    height=540,
    margin=dict(l=0, r=0, t=50, b=0),
)
st.plotly_chart(fig_map, use_container_width=True)

st.subheader("📊 Bảng Pivot Table: Khu vực × Danh mục sản phẩm (Doanh thu)")
pivot_df = pivot_region_category(df_filtered)
st.dataframe(pivot_df.style.format("${:,.2f}"), use_container_width=True)

st.divider()
st.subheader("🚚 Hiệu suất Vận chuyển & Thời gian Giao hàng (Shipping SLA)")
sla_left, sla_right = st.columns(2)

with sla_left:
    fig_ship_box = px.box(
        df_filtered,
        x="Ship Mode",
        y="Shipping_Days",
        color="Ship Mode",
        title="Phân phối Số ngày giao hàng (Shipping Days) theo Hình thức vận chuyển",
        labels={"Ship Mode": "Hình thức giao hàng", "Shipping_Days": "Số ngày giao hàng"},
    )
    fig_ship_box.update_layout(showlegend=False)
    st.plotly_chart(fig_ship_box, use_container_width=True)

with sla_right:
    sla_pivot = (
        df_filtered.pivot_table(
            values="Shipping_Days",
            index="Region",
            columns="Ship Mode",
            aggfunc="mean",
        )
        .round(2)
    )
    fig_sla_heat = px.imshow(
        sla_pivot,
        text_auto=".2f",
        color_continuous_scale="Teal",
        aspect="auto",
        title="Thời gian giao hàng trung bình (Ngày): Khu vực × Hình thức vận chuyển",
        labels={"x": "Hình thức giao hàng", "y": "Khu vực", "color": "Ngày TB"},
    )
    st.plotly_chart(fig_sla_heat, use_container_width=True)
