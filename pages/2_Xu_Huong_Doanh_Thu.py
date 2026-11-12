"""Page 2: Xu hướng doanh thu & Dự báo chuỗi thời gian (Prophet / ARIMA)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.sidebar import init_page, render_global_sidebar
from data.analytics import (
    compute_seasonality_matrix,
    compute_yoy_waterfall,
    forecast_monthly_sales,
    summarize_by_time,
)
from utils.formatters import format_int, format_usd

init_page("Page 2 - Xu hướng & Dự báo", icon="📈")
_, _, df_sidebar = render_global_sidebar()


@st.cache_data(show_spinner="Đang chạy mô hình dự báo doanh thu...")
def cached_forecast(data: pd.DataFrame, horizon: int, method: str) -> tuple[pd.DataFrame, str]:
    """Cache kết quả dự báo chuỗi thời gian để phản hồi nhanh."""
    return forecast_monthly_sales(data, periods=horizon, method=method)


st.title("📈 Page 2: Xu hướng doanh thu & Dự báo tương lai")
st.caption("Theo dõi doanh thu lịch sử bằng biểu đồ đường Plotly và dự báo 3–6 tháng tiếp theo (Prophet / ARIMA).")

if df_sidebar.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc Sidebar hiện tại.")
    st.stop()

# Bộ lọc động trực tiếp trên trang (slider & date_input)
min_date = df_sidebar["Order Date"].min().date()
max_date = df_sidebar["Order Date"].max().date()

ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 1.5])
with ctrl1:
    date_selection = st.date_input(
        "Tinh chỉnh khoảng ngày trên biểu đồ",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
with ctrl2:
    year_min, year_max = int(df_sidebar["Order_Year"].min()), int(df_sidebar["Order_Year"].max())
    if year_min < year_max:
        year_range = st.slider(
            "Khoảng năm hiển thị (Slider)",
            min_value=year_min,
            max_value=year_max,
            value=(year_min, year_max),
        )
    else:
        year_range = (year_min, year_max)
        st.info(f"Dữ liệu đang lọc nằm trong năm {year_min}.")
with ctrl3:
    granularity = st.radio(
        "Mốc tổng hợp",
        options=["Tháng", "Quý", "Năm"],
        horizontal=True,
    )

if isinstance(date_selection, tuple) and len(date_selection) == 2:
    start_dt, end_dt = pd.Timestamp(date_selection[0]), pd.Timestamp(date_selection[1])
else:
    start_dt, end_dt = pd.Timestamp(min_date), pd.Timestamp(max_date)

df_filtered = df_sidebar[
    (df_sidebar["Order Date"] >= start_dt)
    & (df_sidebar["Order Date"] <= end_dt)
    & (df_sidebar["Order_Year"] >= year_range[0])
    & (df_sidebar["Order_Year"] <= year_range[1])
]

if df_filtered.empty:
    st.warning("Không có giao dịch nào trong khoảng thời gian đã chọn.")
    st.stop()

freq_code = {"Tháng": "M", "Quý": "Q", "Năm": "Y"}[granularity]
time_df = summarize_by_time(df_filtered, freq=freq_code)

k1, k2, k3 = st.columns(3)
k1.metric("Doanh thu giai đoạn", format_usd(time_df["Total_Sales"].sum()))
k2.metric("Lợi nhuận giai đoạn", format_usd(time_df["Total_Profit"].sum()))
k3.metric("Số kỳ quan sát", format_int(len(time_df)))

# Biểu đồ đường lịch sử Plotly + Đường trung bình trượt (Moving Average)
show_ma = st.checkbox("Hiển thị đường xu hướng trung bình trượt (Moving Average 3 kỳ)", value=True)
y_cols = ["Total_Sales", "Total_Profit"]
if show_ma and len(time_df) >= 3:
    time_df["Sales_MA3"] = time_df["Total_Sales"].rolling(window=3, min_periods=1).mean()
    y_cols.append("Sales_MA3")

fig_line = px.line(
    time_df,
    x="Period",
    y=y_cols,
    markers=True,
    title=f"Xu hướng Doanh thu, Lợi nhuận & Moving Average theo {granularity}",
    labels={"Period": "Thời gian", "value": "Giá trị (USD)", "variable": "Chỉ số"},
)
fig_line.update_layout(hovermode="x unified")
st.plotly_chart(fig_line, use_container_width=True)

st.divider()
st.subheader("🔮 Dự báo doanh thu 3–6 tháng tiếp theo (Forecasting)")

f_col1, f_col2 = st.columns([1.5, 2])
with f_col1:
    forecast_months = st.slider("Số tháng dự báo tương lai", min_value=3, max_value=6, value=6)
with f_col2:
    forecast_method = st.selectbox(
        "Thuật toán dự báo ưu tiên",
        options=["Prophet (Meta)", "ARIMA / SARIMAX (statsmodels)"],
    )

try:
    fc_df, used_model = cached_forecast(df_filtered, forecast_months, forecast_method)
    hist_part = fc_df[fc_df["Loại dữ liệu"] == "Lịch sử thực tế"]
    pred_part = fc_df[fc_df["Loại dữ liệu"] != "Lịch sử thực tế"]

    fig_fc = go.Figure()
    fig_fc.add_trace(
        go.Scatter(
            x=hist_part["ds"],
            y=hist_part["yhat"],
            mode="lines+markers",
            name="Doanh thu thực tế",
            line=dict(color="#1f77b4", width=2.5),
        )
    )

    # Nối điểm cuối lịch sử với chuỗi dự báo để đường nét đứt liền mạch
    bridge_x = pd.concat([hist_part["ds"].tail(1), pred_part["ds"]])
    bridge_y = pd.concat([hist_part["yhat"].tail(1), pred_part["yhat"]])
    fig_fc.add_trace(
        go.Scatter(
            x=bridge_x,
            y=bridge_y,
            mode="lines+markers",
            name=f"Dự báo ({used_model})",
            line=dict(color="#ff7f0e", width=3, dash="dash"),
        )
    )

    # Vùng tin cậy dự báo
    fig_fc.add_trace(
        go.Scatter(
            x=pd.concat([pred_part["ds"], pred_part["ds"][::-1]]),
            y=pd.concat([pred_part["yhat_upper"], pred_part["yhat_lower"][::-1]]),
            fill="toself",
            fillcolor="rgba(255, 127, 14, 0.16)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="Khoảng tin cậy dự báo",
        )
    )

    fig_fc.update_layout(
        title=f"Dự báo Doanh thu {forecast_months} tháng tiếp theo — Mô hình: {used_model}",
        xaxis_title="Thời gian (Tháng)",
        yaxis_title="Doanh thu (USD)",
        hovermode="x unified",
    )
    st.plotly_chart(fig_fc, use_container_width=True)

    with st.expander("📋 Xem bảng số liệu dự báo chi tiết"):
        pred_display = pred_part[["ds", "yhat", "yhat_lower", "yhat_upper"]].rename(
            columns={
                "ds": "Tháng dự báo",
                "yhat": "Doanh thu dự báo ($)",
                "yhat_lower": "Cận dưới ($)",
                "yhat_upper": "Cận trên ($)",
            }
        )
        pred_display["Tháng dự báo"] = pred_display["Tháng dự báo"].dt.strftime("%Y-%m")
        st.dataframe(
            pred_display.style.format(
                {
                    "Doanh thu dự báo ($)": "${:,.2f}",
                    "Cận dưới ($)": "${:,.2f}",
                    "Cận trên ($)": "${:,.2f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
except ValueError as err:
    st.info(str(err))

st.divider()
st.subheader("🗓️ Bản đồ nhiệt Mùa vụ (Seasonality Heatmap: Năm × Tháng)")
season_metric = st.radio(
    "Chọn chỉ số mùa vụ",
    options=["Sales", "Profit"],
    horizontal=True,
)
season_matrix = compute_seasonality_matrix(df_filtered, metric=season_metric)
if not season_matrix.empty:
    fig_season = px.imshow(
        season_matrix,
        text_auto=".2s",
        color_continuous_scale="Blues" if season_metric == "Sales" else "RdYlGn",
        aspect="auto",
        title=f"Heatmap Mùa vụ {season_metric} theo Năm và Tháng (Nhận diện đỉnh Quý 4)",
        labels={"x": "Tháng", "y": "Năm", "color": f"{season_metric} (USD)"},
    )
    st.plotly_chart(fig_season, use_container_width=True)

st.divider()
st.subheader("📊 Biểu đồ Thác nước Tăng trưởng Qua từng năm (YoY Waterfall)")
wf_df = compute_yoy_waterfall(df_filtered, metric=season_metric)
if len(wf_df) >= 2:
    fig_wf = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=wf_df["Measure"].tolist(),
            x=wf_df["Label"].tolist(),
            y=wf_df["Value"].tolist(),
            text=[f"${v:,.0f}" for v in wf_df["Value"]],
            textposition="outside",
            connector={"line": {"color": "#94a3b8"}},
        )
    )
    fig_wf.update_layout(
        title=f"Biến động tăng/giảm {season_metric} qua các năm (Waterfall Chart)",
        yaxis_title=f"{season_metric} (USD)",
        height=440,
    )
    st.plotly_chart(fig_wf, use_container_width=True)
else:
    st.info("Cần dữ liệu từ 2 năm trở lên để vẽ biểu đồ Waterfall tăng trưởng YoY.")
