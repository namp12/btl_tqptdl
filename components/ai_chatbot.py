"""Thành phần Chatbot AI Phân tích Dữ liệu B2B tích hợp Gemini 3.8 Flash (google-genai)."""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st


def build_dataframe_context(df: pd.DataFrame) -> str:
    """Tạo tóm tắt số liệu thực tế từ DataFrame đang lọc để truyền ngữ cảnh cho Gemini."""
    if df.empty:
        return "Dữ liệu đang lọc hiện đang trống (0 dòng)."

    total_sales = float(df["Sales"].sum())
    total_profit = float(df["Profit"].sum())
    margin = (total_profit / total_sales * 100.0) if total_sales else 0.0
    orders = int(df["Order ID"].nunique())
    customers = int(df["Customer ID"].nunique())
    avg_disc = float(df["Discount"].mean() * 100.0)
    date_min = df["Order Date"].min().strftime("%Y-%m-%d")
    date_max = df["Order Date"].max().strftime("%Y-%m-%d")

    cat_tbl = (
        df.groupby("Category", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Avg_Discount=("Discount", "mean"))
        .round(2)
        .to_string(index=False)
    )

    subcat_tbl = (
        df.groupby(["Category", "Sub-Category"], as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Avg_Discount=("Discount", "mean"))
        .sort_values("Profit", ascending=True)
        .round(2)
        .to_string(index=False)
    )

    region_tbl = (
        df.groupby("Region", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Avg_Discount=("Discount", "mean"))
        .sort_values("Profit", ascending=False)
        .round(2)
        .to_string(index=False)
    )

    worst_state_cat = (
        df.groupby(["State", "Category"], as_index=False)
        .agg(
            Sales=("Sales", "sum"),
            Profit=("Profit", "sum"),
            Avg_Discount=("Discount", "mean"),
            Orders=("Order ID", "nunique"),
        )
        .sort_values("Profit", ascending=True)
        .head(20)
        .round(2)
        .to_string(index=False)
    )

    worst_state_subcat = (
        df.groupby(["State", "Category", "Sub-Category"], as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Avg_Discount=("Discount", "mean"))
        .sort_values("Profit", ascending=True)
        .head(15)
        .round(2)
        .to_string(index=False)
    )

    no_disc = df[df["Discount"] == 0]
    high_disc = df[df["Discount"] > 0.2]
    no_disc_profit = float(no_disc["Profit"].mean()) if len(no_disc) else 0.0
    high_disc_profit = float(high_disc["Profit"].mean()) if len(high_disc) else 0.0
    high_disc_loss_rate = (
        float((high_disc["Profit"] < 0).mean() * 100.0) if len(high_disc) else 0.0
    )

    return (
        f"NGỮ CẢNH DỮ LIỆU SUPERSTORE ĐANG LỌC ({date_min} đến {date_max}, {len(df):,} dòng):\n"
        f"- Tổng doanh thu: ${total_sales:,.2f} | Tổng lợi nhuận: ${total_profit:,.2f} | Biên lợi nhuận: {margin:.2f}%\n"
        f"- Số đơn hàng: {orders:,} | Số khách hàng: {customers:,} | Chiết khấu TB: {avg_disc:.2f}%\n"
        f"- Ảnh hưởng chiết khấu: Discount=0% có lợi nhuận TB ${no_disc_profit:.2f}; "
        f"Discount>20% có lợi nhuận TB ${high_disc_profit:.2f} (tỷ lệ lỗ {high_disc_loss_rate:.2f}%).\n\n"
        f"[1] THEO CATEGORY:\n{cat_tbl}\n\n"
        f"[2] THEO SUB-CATEGORY (tăng dần theo Profit):\n{subcat_tbl}\n\n"
        f"[3] THEO REGION:\n{region_tbl}\n\n"
        f"[4] TOP 20 CẶP STATE x CATEGORY CÓ LỢI NHUẬN THẤP NHẤT:\n{worst_state_cat}\n\n"
        f"[5] TOP 15 CẶP STATE x CATEGORY x SUB-CATEGORY LỖ NẶNG NHẤT:\n{worst_state_subcat}"
    )


def _resolve_api_key() -> str:
    """Lấy GEMINI_API_KEY từ biến môi trường, st.secrets hoặc session_state."""
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    try:
        secret_key = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
        if secret_key:
            return secret_key
    except Exception:
        pass
    return str(st.session_state.get("gemini_api_key_input", "")).strip()


def render_ai_chatbot(df_filtered: pd.DataFrame, location: str = "main") -> None:
    """Hiển thị khung chat trợ lý phân tích dữ liệu B2B sử dụng Gemini 3.8 Flash."""
    container = st.sidebar if location == "sidebar" else st

    container.subheader("🤖 Trợ lý AI Phân tích B2B (Gemini 3.8 Flash)")
    container.caption(
        "Đặt câu hỏi bằng ngôn ngữ tự nhiên dựa trên đúng tập dữ liệu đang lọc hiện tại."
    )

    api_key = _resolve_api_key()
    if not api_key:
        entered_key = container.text_input(
            "Nhập Gemini API Key",
            type="password",
            key="_input_gemini_api_key",
            placeholder="AIza...",
            help="Hoặc thiết lập biến môi trường GEMINI_API_KEY / .streamlit/secrets.toml",
        )
        if entered_key:
            st.session_state["gemini_api_key_input"] = entered_key
            api_key = entered_key.strip()

    if "ai_chat_history" not in st.session_state:
        st.session_state["ai_chat_history"] = []
    if "ai_last_interaction_id" not in st.session_state:
        st.session_state["ai_last_interaction_id"] = None

    sample_questions = [
        "Tại sao lợi nhuận ở bang Texas lại âm và nhóm hàng nào ảnh hưởng nhất?",
        "Đánh giá tác động chiết khấu và đề xuất 3 giải pháp tăng biên lợi nhuận.",
        "Khu vực và ngành hàng nào đang hoạt động hiệu quả nhất?",
    ]

    cols = container.columns(len(sample_questions)) if location == "main" else None
    preset_prompt = None
    if cols is not None:
        for idx, q in enumerate(sample_questions):
            if cols[idx].button(q, key=f"_preset_q_{idx}", use_container_width=True):
                preset_prompt = q

    for msg in st.session_state["ai_chat_history"]:
        with container.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_prompt = container.chat_input("Hỏi AI về số liệu đang hiển thị...")
    final_prompt = preset_prompt or user_prompt

    if not final_prompt:
        return

    st.session_state["ai_chat_history"].append({"role": "user", "content": final_prompt})
    with container.chat_message("user"):
        st.markdown(final_prompt)

    if not api_key:
        reply = "⚠️ Vui lòng nhập `GEMINI_API_KEY` để kết nối với **Gemini 3.8 Flash**."
        st.session_state["ai_chat_history"].append({"role": "assistant", "content": reply})
        with container.chat_message("assistant"):
            st.warning(reply)
        return

    try:
        from google import genai
    except ImportError:
        reply = "⚠️ Thiếu thư viện `google-genai`. Hãy chạy `pip install -U google-genai`."
        st.session_state["ai_chat_history"].append({"role": "assistant", "content": reply})
        with container.chat_message("assistant"):
            st.error(reply)
        return

    data_context = build_dataframe_context(df_filtered)
    system_instruction = (
        "Bạn là Chuyên gia Phân tích Dữ liệu B2B cấp cao đang tư vấn cho Ban Giám đốc Superstore. "
        "Hãy trả lời hoàn toàn bằng tiếng Việt, ngắn gọn, súc tích, chỉ dựa trên số liệu thực tế trong "
        "ngữ cảnh được cung cấp, nêu rõ con số cụ thể (USD, %, chiết khấu) và đưa ra khuyến nghị hành động."
    )

    with container.chat_message("assistant"):
        with st.spinner("Gemini 3.8 Flash đang phân tích dữ liệu..."):
            try:
                client = genai.Client(api_key=api_key)
                prompt_with_context = f"{data_context}\n\nCÂU HỎI CỦA GIÁM ĐỐC:\n{final_prompt}"
                kwargs = {
                    "model": "gemini-3.8-flash",
                    "input": prompt_with_context,
                    "system_instruction": system_instruction,
                }
                if st.session_state.get("ai_last_interaction_id"):
                    kwargs["previous_interaction_id"] = st.session_state["ai_last_interaction_id"]

                interaction = client.interactions.create(**kwargs)
                st.session_state["ai_last_interaction_id"] = interaction.id
                reply = interaction.output_text or "Không nhận được nội dung phản hồi từ mô hình."
                st.markdown(reply)
            except Exception as err:
                reply = f"❌ Lỗi khi gọi Gemini API: {err}"
                st.error(reply)

    st.session_state["ai_chat_history"].append({"role": "assistant", "content": reply})

