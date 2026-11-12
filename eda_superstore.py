"""Script Khám phá, Xử lý Dữ liệu (EDA) & Phân tích Nâng cao cho Sample - Superstore.csv."""

from __future__ import annotations

from data.analytics import (
    compute_rfm_segments,
    forecast_monthly_sales,
    pivot_region_category,
    pivot_year_segment,
    run_market_basket_apriori,
    summarize_by_category,
    summarize_by_region,
    summarize_by_time,
)
from data.loader import audit_raw_data, clean_superstore_data, filter_dataframe, load_raw_data


def main() -> None:
    """Thực thi quy trình kiểm tra, làm sạch, GroupBy, Pivot Table, RFM, Apriori và Forecasting."""
    print("=" * 70)
    print("1. ĐỌC DỮ LIỆU VÀ KIỂM TRA CHẤT LƯỢNG (DATA AUDIT)")
    print("=" * 70)
    raw_df = load_raw_data()
    audit = audit_raw_data(raw_df)
    for key, value in audit.items():
        print(f"- {key}: {value}")

    print("\n" + "=" * 70)
    print("2. LÀM SẠCH & ĐỊNH DẠNG LẠI DỮ LIỆU")
    print("=" * 70)
    clean_df = clean_superstore_data(raw_df, cap_outliers=False)
    print(f"- Kích thước sau làm sạch (loại trùng lặp nghiệp vụ): {clean_df.shape}")
    print(
        clean_df[
            ["Order Date", "Ship Date", "Postal Code", "Sales", "Quantity", "Discount", "Profit"]
        ].dtypes
    )

    print("\n" + "=" * 70)
    print("2.5. THỐNG KÊ MÔ TẢ & LỌC DỮ LIỆU THEO ĐIỀU KIỆN")
    print("=" * 70)
    print(clean_df[["Sales", "Quantity", "Discount", "Profit", "Shipping_Days"]].describe().round(2))

    loss_orders = clean_df[clean_df["Profit"] < 0]
    high_discount_loss = clean_df[(clean_df["Discount"] > 0.2) & (clean_df["Profit"] < 0)]
    west_tech_2017 = filter_dataframe(
        clean_df[clean_df["Order_Year"] == 2017],
        regions=["West"],
        categories=["Technology"],
    )
    print(f"\n- Số dòng giao dịch thua lỗ (Profit < 0): {len(loss_orders)}")
    print(f"- Số dòng chiết khấu > 20% và thua lỗ: {len(high_discount_loss)}")
    print(f"- Số dòng Technology tại khu vực West năm 2017: {len(west_tech_2017)}")

    print("\n" + "=" * 70)
    print("3. THỐNG KÊ GROUPBY & PIVOT TABLE")
    print("=" * 70)
    print("\n[3.1] GroupBy theo Năm (Order_Year):")
    print(summarize_by_time(clean_df, freq="Y").to_string(index=False))

    print("\n[3.2] GroupBy theo Khu vực (Region):")
    print(summarize_by_region(clean_df).to_string(index=False))

    print("\n[3.3] GroupBy theo Danh mục (Category & Sub-Category):")
    print(summarize_by_category(clean_df).to_string(index=False))

    print("\n[3.4] Pivot Table Doanh thu: Khu vực (Region) x Danh mục (Category):")
    print(pivot_region_category(clean_df).round(2))

    print("\n[3.5] Pivot Table Doanh thu & Số đơn hàng: Năm x Phân khúc (Segment):")
    print(pivot_year_segment(clean_df).round(2))

    print("\n" + "=" * 70)
    print("4. PHÂN TÍCH NÂNG CAO (RFM, APRIORI, FORECASTING)")
    print("=" * 70)
    rfm_df = compute_rfm_segments(clean_df)
    print("\n[4.1] Phân khúc khách hàng RFM:")
    print(rfm_df["RFM_Segment"].value_counts().to_string())

    rules_df = run_market_basket_apriori(clean_df, item_col="Sub-Category")
    print("\n[4.2] Top 10 Luật kết hợp Giỏ hàng (Apriori - Sub-Category):")
    print(rules_df.head(10).to_string(index=False))

    fc_df, model_name = forecast_monthly_sales(clean_df, periods=6)
    print(f"\n[4.3] Dự báo 6 tháng tiếp theo ({model_name}):")
    print(fc_df[fc_df["Loại dữ liệu"] != "Lịch sử thực tế"].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
