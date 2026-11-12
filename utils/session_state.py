"""Quản lý và đồng bộ st.session_state toàn cục giữa các trang Streamlit."""

from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st


def init_global_state(df: pd.DataFrame) -> None:
    """Khởi tạo các khóa trạng thái dùng chung nếu chưa tồn tại trong st.session_state."""
    min_date = df["Order Date"].min().date()
    max_date = df["Order Date"].max().date()
    all_regions = sorted(df["Region"].unique().tolist())
    all_categories = sorted(df["Category"].unique().tolist())
    all_segments = sorted(df["Segment"].unique().tolist())

    defaults: dict[str, object] = {
        "ss_cap_outliers": False,
        "ss_date_range": (min_date, max_date),
        "ss_regions": all_regions,
        "ss_categories": all_categories,
        "ss_segments": all_segments,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def reset_global_state(df: pd.DataFrame) -> None:
    """Đặt lại toàn bộ bộ lọc toàn cục về giá trị mặc định ban đầu."""
    st.session_state["ss_cap_outliers"] = False
    st.session_state["ss_date_range"] = (
        df["Order Date"].min().date(),
        df["Order Date"].max().date(),
    )
    st.session_state["ss_regions"] = sorted(df["Region"].unique().tolist())
    st.session_state["ss_categories"] = sorted(df["Category"].unique().tolist())
    st.session_state["ss_segments"] = sorted(df["Segment"].unique().tolist())
    for widget_key in ("_w_cap_outliers", "_w_date_range", "_w_regions", "_w_categories", "_w_segments"):
        st.session_state.pop(widget_key, None)


def get_date_range_timestamps() -> tuple[pd.Timestamp, pd.Timestamp] | None:
    """Trả về khoảng thời gian dạng pd.Timestamp từ global state."""
    date_val = st.session_state.get("ss_date_range")
    if isinstance(date_val, (tuple, list)) and len(date_val) == 2:
        start, end = date_val[0], date_val[1]
        if isinstance(start, dt.date) and isinstance(end, dt.date):
            return pd.Timestamp(start), pd.Timestamp(end)
    return None
