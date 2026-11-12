"""Thành phần Sidebar dùng chung với đồng bộ st.session_state xuyên suốt 5 trang."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from data.loader import filter_dataframe, get_cached_superstore_data
from utils.session_state import (
    get_date_range_timestamps,
    init_global_state,
    reset_global_state,
)


def init_page(title: str, icon: str = "📊") -> None:
    """Thiết lập cấu hình chuẩn cho từng trang Dashboard."""
    st.set_page_config(
        page_title=f"{title} | Superstore BI",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def _sync_key(widget_key: str, state_key: str) -> None:
    """Callback sao chép giá trị từ widget sang global session_state."""
    st.session_state[state_key] = st.session_state[widget_key]


def render_global_sidebar(
    include_date: bool = True,
    include_region: bool = True,
    include_category: bool = True,
    include_segment: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    """Hiển thị Sidebar toàn cục được đồng bộ bằng st.session_state và trả về (df_clean, audit, df_filtered)."""
    # Đọc tạm dữ liệu theo trạng thái cap_outliers hiện tại
    cap_flag = bool(st.session_state.get("ss_cap_outliers", False))
    df_clean, audit = get_cached_superstore_data(cap_outliers=cap_flag)
    init_global_state(df_clean)

    min_dt = df_clean["Order Date"].min().date()
    max_dt = df_clean["Order Date"].max().date()
    all_regions = sorted(df_clean["Region"].unique().tolist())
    all_categories = sorted(df_clean["Category"].unique().tolist())
    all_segments = sorted(df_clean["Segment"].unique().tolist())

    with st.sidebar:
        st.header("🎛️ Bộ lọc đồng bộ toàn cục")
        st.caption("Mọi lựa chọn được lưu vào `st.session_state` và giữ nguyên khi chuyển trang.")

        if st.button("🔄 Đặt lại bộ lọc mặc định", use_container_width=True):
            reset_global_state(df_clean)
            st.rerun()

        st.checkbox(
            "Chặn trần ngoại lệ (IQR Winsorize)",
            value=bool(st.session_state["ss_cap_outliers"]),
            key="_w_cap_outliers",
            on_change=_sync_key,
            args=("_w_cap_outliers", "ss_cap_outliers"),
            help="Giới hạn các giá trị Sales/Profit vượt 1.5×IQR để giảm nhiễu cực trị.",
        )

        if include_date:
            saved_dates = st.session_state["ss_date_range"]
            st.date_input(
                "Khoảng ngày đặt hàng",
                value=saved_dates,
                min_value=min_dt,
                max_value=max_dt,
                key="_w_date_range",
                on_change=_sync_key,
                args=("_w_date_range", "ss_date_range"),
            )

        if include_region:
            st.multiselect(
                "Khu vực (Region)",
                options=all_regions,
                default=st.session_state["ss_regions"],
                key="_w_regions",
                on_change=_sync_key,
                args=("_w_regions", "ss_regions"),
            )

        if include_category:
            st.multiselect(
                "Danh mục (Category)",
                options=all_categories,
                default=st.session_state["ss_categories"],
                key="_w_categories",
                on_change=_sync_key,
                args=("_w_categories", "ss_categories"),
            )

        if include_segment:
            st.multiselect(
                "Phân khúc (Segment)",
                options=all_segments,
                default=st.session_state["ss_segments"],
                key="_w_segments",
                on_change=_sync_key,
                args=("_w_segments", "ss_segments"),
            )

        # Tóm tắt state đang hoạt động
        active_dates = get_date_range_timestamps()
        date_text = (
            f"{active_dates[0].strftime('%d/%m/%Y')} → {active_dates[1].strftime('%d/%m/%Y')}"
            if active_dates
            else "Toàn thời gian"
        )
        st.divider()
        st.markdown(
            f"**State đang giữ:**\n"
            f"- 📅 `{date_text}`\n"
            f"- 🗺️ Khu vực: `{len(st.session_state['ss_regions'])}/{len(all_regions)}`\n"
            f"- 📦 Danh mục: `{len(st.session_state['ss_categories'])}/{len(all_categories)}`"
        )

    df_filtered = filter_dataframe(
        df_clean,
        date_range=get_date_range_timestamps() if include_date else None,
        regions=st.session_state["ss_regions"] if include_region else None,
        categories=st.session_state["ss_categories"] if include_category else None,
        segments=st.session_state["ss_segments"] if include_segment else None,
    )
    return df_clean, audit, df_filtered

