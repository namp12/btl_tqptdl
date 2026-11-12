"""Kiểm thử đơn vị (Unit Tests) cho tầng xử lý dữ liệu và phân tích nâng cao."""

from __future__ import annotations

import pandas as pd

from data.analytics import (
    compute_cohort_retention,
    compute_kmeans_clusters,
    compute_pareto_abc,
    compute_rfm_segments,
    compute_seasonality_matrix,
    compute_yoy_waterfall,
    detect_loss_anomalies,
    forecast_monthly_sales,
    pivot_region_category,
    pivot_year_segment,
    run_market_basket_apriori,
    simulate_discount_what_if,
    summarize_by_category,
    summarize_by_region,
    summarize_by_state,
    summarize_by_time,
    summarize_top_products,
)
from data.loader import audit_raw_data, clean_superstore_data, filter_dataframe, load_raw_data


def _get_clean_df() -> pd.DataFrame:
    raw = load_raw_data()
    return clean_superstore_data(raw, cap_outliers=False)


def test_load_audit_and_clean() -> None:
    raw = load_raw_data()
    assert raw.shape == (9994, 21)

    audit = audit_raw_data(raw)
    assert audit["missing_total"] == 0
    assert audit["business_duplicates"] == 1
    assert audit["invalid_ship_sequence"] == 0

    clean = clean_superstore_data(raw, cap_outliers=False)
    assert clean.shape[0] == 9993
    assert pd.api.types.is_datetime64_any_dtype(clean["Order Date"])
    assert pd.api.types.is_datetime64_any_dtype(clean["Ship Date"])
    assert clean["Postal Code"].str.len().eq(5).all()


def test_filtering_and_aggregations() -> None:
    clean = _get_clean_df()
    west_tech = filter_dataframe(clean, regions=["West"], categories=["Technology"])
    assert not west_tech.empty
    assert set(west_tech["Region"].unique()) == {"West"}
    assert set(west_tech["Category"].unique()) == {"Technology"}

    assert not summarize_by_time(clean, freq="Y").empty
    assert not summarize_by_region(clean).empty
    assert not summarize_by_state(clean).empty
    assert not summarize_by_category(clean).empty
    assert len(summarize_top_products(clean, top_n=10)) == 10
    assert "Tổng cộng" in pivot_region_category(clean).index
    assert not pivot_year_segment(clean).empty


def test_advanced_analytics() -> None:
    clean = _get_clean_df()

    rfm = compute_rfm_segments(clean)
    assert len(rfm) == 793
    assert "RFM_Segment" in rfm.columns

    km = compute_kmeans_clusters(clean, n_clusters=4)
    assert km["Cluster_Label"].nunique() == 4

    cohort = compute_cohort_retention(clean)
    assert not cohort.empty

    season = compute_seasonality_matrix(clean, metric="Sales")
    assert season.shape[0] == 4

    wf = compute_yoy_waterfall(clean, metric="Sales")
    assert not wf.empty

    abc = compute_pareto_abc(clean, entity_col="Sub-Category")
    assert not abc.empty
    assert abc["Cumulative_Sales_Pct"].iloc[-1] <= 100.01

    sim = simulate_discount_what_if(clean, max_discount_cap=0.20, loss_subcat_uplift_pct=5.0)
    assert sim["sim_profit"] > sim["actual_profit"]
    assert sim["sim_loss_rows"] < sim["actual_loss_rows"]

    anomalies = detect_loss_anomalies(clean, profit_threshold=-100.0)
    assert not anomalies.empty
    assert (anomalies["Profit"] <= -100.0).all()

    rules = run_market_basket_apriori(clean, item_col="Sub-Category", min_support=0.015, min_confidence=0.2)
    assert not rules.empty

    fc, _ = forecast_monthly_sales(clean, periods=6, method="ARIMA")
    assert len(fc[fc["Loại dữ liệu"] != "Lịch sử thực tế"]) == 6
