"""Module phân tích thống kê (GroupBy, Pivot Table) và phân tích nâng cao (Forecasting, RFM, Apriori)."""

from __future__ import annotations

from collections import Counter
from itertools import combinations

import numpy as np
import pandas as pd

from utils.formatters import US_STATE_TO_CODE


def summarize_by_time(df: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    """Tổng hợp doanh thu, lợi nhuận và số đơn hàng theo mốc thời gian (M, Q, Y)."""
    freq_col_map = {
        "M": "Order_YearMonth",
        "Q": "Order_YearQuarter",
        "Y": "Order_Year",
    }
    if freq not in freq_col_map:
        raise ValueError("freq phải là 'M', 'Q' hoặc 'Y'.")

    time_col = freq_col_map[freq]
    summary = (
        df.groupby(time_col, as_index=False)
        .agg(
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum"),
            Order_Count=("Order ID", "nunique"),
            Total_Quantity=("Quantity", "sum"),
        )
        .rename(columns={time_col: "Period"})
        .sort_values("Period")
    )
    summary["Profit_Margin_Pct"] = np.where(
        summary["Total_Sales"] != 0,
        (summary["Total_Profit"] / summary["Total_Sales"]) * 100.0,
        0.0,
    )
    return summary


def summarize_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """Tổng hợp doanh thu, lợi nhuận và số đơn hàng theo khu vực (Region)."""
    summary = (
        df.groupby("Region", as_index=False)
        .agg(
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum"),
            Order_Count=("Order ID", "nunique"),
            Total_Quantity=("Quantity", "sum"),
        )
        .sort_values("Total_Sales", ascending=False)
    )
    summary["Profit_Margin_Pct"] = np.where(
        summary["Total_Sales"] != 0,
        (summary["Total_Profit"] / summary["Total_Sales"]) * 100.0,
        0.0,
    )
    return summary


def summarize_by_state(df: pd.DataFrame) -> pd.DataFrame:
    """Tổng hợp doanh thu, lợi nhuận theo tiểu bang kèm mã bang 2 ký tự cho Choropleth Map."""
    summary = (
        df.groupby(["State", "Region"], as_index=False)
        .agg(
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum"),
            Order_Count=("Order ID", "nunique"),
            Total_Quantity=("Quantity", "sum"),
        )
        .sort_values("Total_Sales", ascending=False)
    )
    summary["State_Code"] = summary["State"].map(US_STATE_TO_CODE)
    summary["Profit_Margin_Pct"] = np.where(
        summary["Total_Sales"] != 0,
        (summary["Total_Profit"] / summary["Total_Sales"]) * 100.0,
        0.0,
    )
    return summary


def summarize_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Tổng hợp doanh thu, lợi nhuận theo Category và Sub-Category."""
    summary = (
        df.groupby(["Category", "Sub-Category"], as_index=False)
        .agg(
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum"),
            Order_Count=("Order ID", "nunique"),
            Total_Quantity=("Quantity", "sum"),
        )
        .sort_values("Total_Sales", ascending=False)
    )
    summary["Profit_Margin_Pct"] = np.where(
        summary["Total_Sales"] != 0,
        (summary["Total_Profit"] / summary["Total_Sales"]) * 100.0,
        0.0,
    )
    return summary


def summarize_top_products(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Lọc Top N sản phẩm có doanh thu cao nhất."""
    return (
        df.groupby(["Product ID", "Product Name", "Category"], as_index=False)
        .agg(
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum"),
            Order_Count=("Order ID", "nunique"),
            Total_Quantity=("Quantity", "sum"),
        )
        .sort_values("Total_Sales", ascending=False)
        .head(top_n)
    )


def pivot_region_category(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot Table doanh thu theo Khu vực (hàng) × Danh mục sản phẩm (cột)."""
    return pd.pivot_table(
        df,
        values="Sales",
        index="Region",
        columns="Category",
        aggfunc="sum",
        fill_value=0.0,
        margins=True,
        margins_name="Tổng cộng",
    )


def pivot_year_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot Table doanh thu và số đơn hàng theo Năm × Phân khúc."""
    return pd.pivot_table(
        df,
        values=["Sales", "Order ID"],
        index="Order_Year",
        columns="Segment",
        aggfunc={"Sales": "sum", "Order ID": "nunique"},
        fill_value=0.0,
    )


def forecast_monthly_sales(
    df: pd.DataFrame,
    periods: int = 6,
    method: str = "Prophet (Meta)",
) -> tuple[pd.DataFrame, str]:
    """Dự báo doanh thu theo tháng cho 3–6 tháng tiếp theo bằng Prophet hoặc ARIMA."""
    monthly = (
        df.set_index("Order Date")["Sales"]
        .resample("MS")
        .sum()
        .reset_index()
        .rename(columns={"Order Date": "ds", "Sales": "y"})
    )
    if len(monthly) < 6:
        raise ValueError("Cần tối thiểu 6 tháng dữ liệu lịch sử để thực hiện dự báo.")

    last_date = monthly["ds"].max()
    future_dates = pd.date_range(last_date + pd.offsets.MonthBegin(1), periods=periods, freq="MS")

    hist_df = monthly.rename(columns={"y": "yhat"}).copy()
    hist_df["yhat_lower"] = hist_df["yhat"]
    hist_df["yhat_upper"] = hist_df["yhat"]
    hist_df["Loại dữ liệu"] = "Lịch sử thực tế"

    # 1. Thử Prophet nếu người dùng chọn
    if "Prophet" in method:
        try:
            from prophet import Prophet  # type: ignore

            model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
            model.fit(monthly)
            future = model.make_future_dataframe(periods=periods, freq="MS")
            pred = model.predict(future).tail(periods)[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
            pred["yhat"] = pred["yhat"].clip(lower=0.0)
            pred["yhat_lower"] = pred["yhat_lower"].clip(lower=0.0)
            pred["Loại dữ liệu"] = "Dự báo (Prophet)"
            return pd.concat([hist_df, pred], ignore_index=True), "Prophet (Meta)"
        except Exception:
            pass

    # 2. Thử ARIMA / SARIMAX (statsmodels)
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX  # type: ignore

        seasonal_order = (1, 0, 1, 12) if len(monthly) >= 24 else (0, 0, 0, 0)
        model = SARIMAX(
            monthly["y"],
            order=(1, 1, 1),
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fit_res = model.fit(disp=False)
        fc = fit_res.get_forecast(steps=periods)
        ci = fc.conf_int(alpha=0.05)
        pred = pd.DataFrame(
            {
                "ds": future_dates,
                "yhat": np.clip(fc.predicted_mean.to_numpy(), 0.0, None),
                "yhat_lower": np.clip(ci.iloc[:, 0].to_numpy(), 0.0, None),
                "yhat_upper": np.clip(ci.iloc[:, 1].to_numpy(), 0.0, None),
                "Loại dữ liệu": "Dự báo (ARIMA/SARIMAX)",
            }
        )
        return pd.concat([hist_df, pred], ignore_index=True), "ARIMA / SARIMAX (statsmodels)"
    except Exception:
        pass

    # 3. Fallback nhẹ bằng Xu hướng tuyến tính + Mùa vụ tháng (luôn chạy không phụ thuộc thư viện C++)
    y = monthly["y"].to_numpy(dtype=float)
    x = np.arange(len(y), dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    trend = intercept + slope * x
    residuals = y - trend

    monthly["month_num"] = monthly["ds"].dt.month
    seasonal_map = (
        pd.DataFrame({"m": monthly["month_num"], "res": residuals})
        .groupby("m")["res"]
        .mean()
        .to_dict()
    )
    resid_std = float(np.std(residuals))

    future_x = np.arange(len(y), len(y) + periods, dtype=float)
    future_yhat = []
    for idx_step, dt_val in enumerate(future_dates):
        val = (intercept + slope * future_x[idx_step]) + seasonal_map.get(dt_val.month, 0.0)
        future_yhat.append(max(0.0, float(val)))

    future_yhat_arr = np.array(future_yhat)
    pred = pd.DataFrame(
        {
            "ds": future_dates,
            "yhat": future_yhat_arr,
            "yhat_lower": np.clip(future_yhat_arr - 1.64 * resid_std, 0.0, None),
            "yhat_upper": future_yhat_arr + 1.64 * resid_std,
            "Loại dữ liệu": "Dự báo (Seasonal Trend)",
        }
    )
    return pd.concat([hist_df, pred], ignore_index=True), "Seasonal Linear Trend (Fallback)"


def _score_quintiles(series: pd.Series, ascending: bool = True) -> pd.Series:
    """Chia điểm 1-5 ổn định ngay cả khi phân phối có nhiều giá trị trùng nhau."""
    ranked = series.rank(method="first", ascending=True)
    labels = [1, 2, 3, 4, 5] if ascending else [5, 4, 3, 2, 1]
    bins = pd.qcut(ranked, q=min(5, len(series)), labels=False, duplicates="drop")
    max_bin = int(bins.max()) if len(bins) else 0
    if max_bin == 4:
        return bins.map(lambda b: labels[int(b)]).astype(int)
    # Chuẩn hóa về thang 1..5 nếu số lượng khách hàng quá ít
    scaled = np.ceil(((bins + 1) / (max_bin + 1)) * 5).astype(int)
    return scaled if ascending else (6 - scaled)


def compute_rfm_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Tính chỉ số RFM (Recency, Frequency, Monetary) và phân nhóm khách hàng tự động."""
    snapshot_date = df["Order Date"].max() + pd.Timedelta(days=1)
    rfm = (
        df.groupby(["Customer ID", "Customer Name", "Segment"], as_index=False)
        .agg(
            Last_Order_Date=("Order Date", "max"),
            Frequency=("Order ID", "nunique"),
            Monetary=("Sales", "sum"),
            Total_Profit=("Profit", "sum"),
        )
    )
    rfm["Recency"] = (snapshot_date - rfm["Last_Order_Date"]).dt.days

    if len(rfm) < 5:
        rfm["R_Score"] = 3
        rfm["F_Score"] = 3
        rfm["M_Score"] = 3
    else:
        rfm["R_Score"] = _score_quintiles(rfm["Recency"], ascending=False)
        rfm["F_Score"] = _score_quintiles(rfm["Frequency"], ascending=True)
        rfm["M_Score"] = _score_quintiles(rfm["Monetary"], ascending=True)

    rfm["RFM_Total"] = rfm["R_Score"] + rfm["F_Score"] + rfm["M_Score"]

    def _assign_label(row: pd.Series) -> str:
        r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "VIP"
        if f >= 4 and r >= 3:
            return "Khách hàng trung thành"
        if r >= 4 and f <= 2:
            return "Khách hàng mới"
        if r <= 2 and (f >= 3 or m >= 3):
            return "Nguy cơ rời bỏ"
        if r <= 2 and f <= 2:
            return "Ngủ đông / Cần kích hoạt"
        return "Khách hàng tiềm năng"

    rfm["RFM_Segment"] = rfm.apply(_assign_label, axis=1)
    return rfm.sort_values("Monetary", ascending=False).reset_index(drop=True)


def run_market_basket_apriori(
    df: pd.DataFrame,
    item_col: str = "Sub-Category",
    min_support: float = 0.015,
    min_confidence: float = 0.2,
) -> pd.DataFrame:
    """Phân tích giỏ hàng (Market Basket Analysis) tìm luật kết hợp bán chéo (Apriori)."""
    baskets = df.groupby("Order ID")[item_col].apply(lambda s: sorted(set(s.astype(str)))).tolist()
    total_orders = len(baskets)
    if total_orders == 0:
        return pd.DataFrame()

    # Thử dùng mlxtend trước nếu môi trường có cài đặt
    try:
        from mlxtend.frequent_patterns import apriori, association_rules  # type: ignore
        from mlxtend.preprocessing import TransactionEncoder  # type: ignore

        te = TransactionEncoder()
        te_ary = te.fit(baskets).transform(baskets)
        basket_df = pd.DataFrame(te_ary, columns=te.columns_)
        freq_items = apriori(basket_df, min_support=min_support, use_colnames=True)
        if not freq_items.empty:
            rules = association_rules(freq_items, metric="confidence", min_threshold=min_confidence)
            if not rules.empty:
                rules = rules.sort_values(["lift", "confidence"], ascending=False).copy()
                rules["Antecedents"] = rules["antecedents"].apply(lambda x: ", ".join(sorted(x)))
                rules["Consequents"] = rules["consequents"].apply(lambda x: ", ".join(sorted(x)))
                rules["Pair_Orders"] = (rules["support"] * total_orders).round().astype(int)
                return rules[
                    ["Antecedents", "Consequents", "Pair_Orders", "support", "confidence", "lift"]
                ].rename(
                    columns={
                        "support": "Support",
                        "confidence": "Confidence",
                        "lift": "Lift",
                    }
                ).reset_index(drop=True)
    except Exception:
        pass

    # Thuật toán Apriori thuần Python (tìm cặp 2 sản phẩm thường mua cùng nhau)
    single_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    for items in baskets:
        for item in items:
            single_counts[item] += 1
        if len(items) >= 2:
            for a, b in combinations(items, 2):
                pair_counts[(a, b)] += 1

    rows = []
    for (a, b), pair_cnt in pair_counts.items():
        support = pair_cnt / total_orders
        if support < min_support:
            continue
        sup_a = single_counts[a] / total_orders
        sup_b = single_counts[b] / total_orders

        conf_a_b = pair_cnt / single_counts[a]
        lift_a_b = conf_a_b / sup_b if sup_b else 0.0
        if conf_a_b >= min_confidence:
            rows.append(
                {
                    "Antecedents": a,
                    "Consequents": b,
                    "Pair_Orders": pair_cnt,
                    "Support": round(support, 4),
                    "Confidence": round(conf_a_b, 4),
                    "Lift": round(lift_a_b, 4),
                }
            )

        conf_b_a = pair_cnt / single_counts[b]
        lift_b_a = conf_b_a / sup_a if sup_a else 0.0
        if conf_b_a >= min_confidence:
            rows.append(
                {
                    "Antecedents": b,
                    "Consequents": a,
                    "Pair_Orders": pair_cnt,
                    "Support": round(support, 4),
                    "Confidence": round(conf_b_a, 4),
                    "Lift": round(lift_b_a, 4),
                }
            )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["Lift", "Confidence"], ascending=False).reset_index(drop=True)


def compute_cohort_retention(df: pd.DataFrame) -> pd.DataFrame:
    """Tính ma trận tỷ lệ giữ chân khách hàng theo năm gia nhập (Cohort Retention %)."""
    if df.empty:
        return pd.DataFrame()

    cohort_df = df[["Customer ID", "Order_Year"]].drop_duplicates().copy()
    cohort_df["Cohort_Year"] = cohort_df.groupby("Customer ID")["Order_Year"].transform("min")
    cohort_df["Cohort_Index"] = cohort_df["Order_Year"] - cohort_df["Cohort_Year"]

    counts = (
        cohort_df.groupby(["Cohort_Year", "Cohort_Index"])["Customer ID"]
        .nunique()
        .unstack(fill_value=0)
        .sort_index()
    )
    if 0 not in counts.columns:
        return pd.DataFrame()

    cohort_sizes = counts[0].replace(0, np.nan)
    retention = counts.div(cohort_sizes, axis=0) * 100.0
    retention.columns = [f"Năm +{int(c)}" if c > 0 else "Năm 0 (Gốc)" for c in retention.columns]
    retention.index = [f"Cohort {int(y)}" for y in retention.index]
    return retention.round(1)


def compute_seasonality_matrix(df: pd.DataFrame, metric: str = "Sales") -> pd.DataFrame:
    """Tạo ma trận mùa vụ Năm × Tháng cho Heatmap phân tích chu kỳ."""
    if df.empty:
        return pd.DataFrame()
    pivot = pd.pivot_table(
        df,
        values=metric,
        index="Order_Year",
        columns="Order_Month",
        aggfunc="sum",
        fill_value=0.0,
    )
    pivot.columns = [f"Tháng {int(m)}" for m in pivot.columns]
    return pivot


def compute_pareto_abc(df: pd.DataFrame, entity_col: str = "Product Name") -> pd.DataFrame:
    """Phân tích Pareto 80/20 (ABC Classification) theo doanh thu cho sản phẩm hoặc khách hàng."""
    if df.empty:
        return pd.DataFrame()

    grouped = (
        df.groupby(entity_col, as_index=False)
        .agg(
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum"),
            Order_Count=("Order ID", "nunique"),
        )
        .sort_values("Total_Sales", ascending=False)
        .reset_index(drop=True)
    )
    total_sales = float(grouped["Total_Sales"].sum())
    if total_sales <= 0:
        return pd.DataFrame()

    grouped["Sales_Share_Pct"] = (grouped["Total_Sales"] / total_sales) * 100.0
    grouped["Cumulative_Sales_Pct"] = grouped["Sales_Share_Pct"].cumsum()
    grouped["Rank"] = np.arange(1, len(grouped) + 1)

    def _abc_class(cum_pct: float) -> str:
        if cum_pct <= 80.0:
            return "Nhóm A (Top 80% doanh thu)"
        if cum_pct <= 95.0:
            return "Nhóm B (80% – 95%)"
        return "Nhóm C (5% cuối)"

    grouped["ABC_Class"] = grouped["Cumulative_Sales_Pct"].apply(_abc_class)
    return grouped


def simulate_discount_what_if(
    df: pd.DataFrame,
    max_discount_cap: float = 0.20,
    loss_subcat_uplift_pct: float = 0.0,
) -> dict[str, float | int]:
    """Mô phỏng kịch bản What-If: đặt trần chiết khấu tối đa và điều chỉnh giá nhóm lỗ."""
    if df.empty:
        return {
            "actual_sales": 0.0,
            "sim_sales": 0.0,
            "actual_profit": 0.0,
            "sim_profit": 0.0,
            "profit_gain": 0.0,
            "actual_loss_rows": 0,
            "sim_loss_rows": 0,
            "actual_margin_pct": 0.0,
            "sim_margin_pct": 0.0,
        }

    sim = df[["Sales", "Discount", "Profit", "Sub-Category"]].copy()
    # Suy ra giá vốn giao dịch và giá niêm yết gốc trước chiết khấu
    implied_cost = sim["Sales"] - sim["Profit"]
    safe_disc = np.clip(sim["Discount"], 0.0, 0.99)
    gross_price = sim["Sales"] / (1.0 - safe_disc)

    new_disc = np.minimum(safe_disc, max_discount_cap)
    uplift_mask = sim["Sub-Category"].isin(["Tables", "Bookcases", "Supplies"])
    uplift_mult = np.where(uplift_mask, 1.0 + (loss_subcat_uplift_pct / 100.0), 1.0)

    sim_sales = gross_price * (1.0 - new_disc) * uplift_mult
    sim_profit = sim_sales - implied_cost

    actual_sales = float(sim["Sales"].sum())
    actual_profit = float(sim["Profit"].sum())
    total_sim_sales = float(sim_sales.sum())
    total_sim_profit = float(sim_profit.sum())

    return {
        "actual_sales": actual_sales,
        "sim_sales": total_sim_sales,
        "actual_profit": actual_profit,
        "sim_profit": total_sim_profit,
        "profit_gain": total_sim_profit - actual_profit,
        "actual_loss_rows": int((sim["Profit"] < 0).sum()),
        "sim_loss_rows": int((sim_profit < 0).sum()),
        "actual_margin_pct": (actual_profit / actual_sales * 100.0) if actual_sales else 0.0,
        "sim_margin_pct": (total_sim_profit / total_sim_sales * 100.0) if total_sim_sales else 0.0,
    }


def detect_loss_anomalies(df: pd.DataFrame, profit_threshold: float = -100.0) -> pd.DataFrame:
    """Phát hiện các dòng giao dịch thua lỗ nghiêm trọng kèm phân loại nguyên nhân gốc rễ."""
    anomalies = df[df["Profit"] <= profit_threshold].copy()
    if anomalies.empty:
        return anomalies

    def _root_cause(row: pd.Series) -> str:
        high_disc = row["Discount"] > 0.20
        loss_subcat = row["Sub-Category"] in ("Tables", "Bookcases", "Supplies")
        if high_disc and loss_subcat:
            return "Chiết khấu >20% & Nhóm hàng lỗ"
        if high_disc:
            return "Chiết khấu sâu (>20%)"
        if loss_subcat:
            return "Nhóm hàng biên âm (Tables/Bookcases/Supplies)"
        return "Giá vốn/Chi phí vận chuyển cao"

    anomalies["Nguyên_Nhân_Gợi_Ý"] = anomalies.apply(_root_cause, axis=1)
    cols = [
        "Order ID",
        "Order Date",
        "State",
        "Region",
        "Category",
        "Sub-Category",
        "Product Name",
        "Sales",
        "Discount",
        "Profit",
        "Nguyên_Nhân_Gợi_Ý",
    ]
    return anomalies[cols].sort_values("Profit", ascending=True).reset_index(drop=True)


def compute_kmeans_clusters(df: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    """Phân cụm khách hàng không giám sát (K-Means) trên không gian RFM chuẩn hóa."""
    rfm = compute_rfm_segments(df)
    if len(rfm) < max(3, n_clusters):
        return rfm.assign(Cluster_Label="Cluster 0")

    features = np.column_stack(
        [
            rfm["Recency"].to_numpy(dtype=float),
            np.log1p(rfm["Frequency"].to_numpy(dtype=float)),
            np.log1p(np.clip(rfm["Monetary"].to_numpy(dtype=float), 0.0, None)),
        ]
    )
    means = features.mean(axis=0)
    stds = np.where(features.std(axis=0) == 0, 1.0, features.std(axis=0))
    scaled = (features - means) / stds

    labels: np.ndarray
    try:
        from sklearn.cluster import KMeans  # type: ignore

        km = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        labels = km.fit_predict(scaled)
    except Exception:
        # Thuật toán K-Means thuần NumPy dự phòng khi chưa cài scikit-learn
        rng = np.random.default_rng(42)
        init_idx = rng.choice(len(scaled), size=n_clusters, replace=False)
        centroids = scaled[init_idx].copy()
        labels = np.zeros(len(scaled), dtype=int)
        for _ in range(50):
            dists = np.linalg.norm(scaled[:, None, :] - centroids[None, :, :], axis=2)
            new_labels = np.argmin(dists, axis=1)
            if np.array_equal(new_labels, labels):
                break
            labels = new_labels
            for c_id in range(n_clusters):
                mask = labels == c_id
                if mask.any():
                    centroids[c_id] = scaled[mask].mean(axis=0)

    rfm = rfm.copy()
    rfm["Cluster_ID"] = labels
    # Sắp xếp nhãn cụm theo Monetary trung bình giảm dần để đặt tên nhất quán
    order = (
        rfm.groupby("Cluster_ID")["Monetary"]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    rank_map = {cid: f"Cụm {idx + 1}" for idx, cid in enumerate(order)}
    rfm["Cluster_Label"] = rfm["Cluster_ID"].map(rank_map)
    return rfm


def compute_yoy_waterfall(df: pd.DataFrame, metric: str = "Sales") -> pd.DataFrame:
    """Tính biến động tăng/giảm tuyệt đối qua từng năm (YoY Delta) cho biểu đồ Waterfall."""
    if df.empty or metric not in ("Sales", "Profit"):
        return pd.DataFrame()

    yearly = (
        df.groupby("Order_Year", as_index=False)[metric]
        .sum()
        .sort_values("Order_Year")
        .reset_index(drop=True)
    )
    if yearly.empty:
        return pd.DataFrame()

    rows = []
    for idx, row in yearly.iterrows():
        yr = int(row["Order_Year"])
        val = float(row[metric])
        if idx == 0:
            rows.append({"Label": f"Năm {yr} (Gốc)", "Value": val, "Measure": "absolute", "Total": val})
        else:
            prev_val = float(yearly.loc[idx - 1, metric])
            delta = val - prev_val
            rows.append({"Label": f"Thay đổi {yr}", "Value": delta, "Measure": "relative", "Total": val})

    if len(yearly) > 1:
        last_yr = int(yearly.iloc[-1]["Order_Year"])
        last_val = float(yearly.iloc[-1][metric])
        rows.append({"Label": f"Tổng năm {last_yr}", "Value": last_val, "Measure": "total", "Total": last_val})

    return pd.DataFrame(rows)



