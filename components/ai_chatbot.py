"""Thành phần Chatbot AI Phân tích Dữ liệu B2B hỗ trợ Google Gemini API & Oxion AI (cc_...)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

import pandas as pd
import streamlit as st

OXION_BASE_URL = "https://oxionai.com/v1"


def build_dataframe_context(df: pd.DataFrame) -> str:
    """Tạo tóm tắt số liệu thực tế từ DataFrame đang lọc để truyền ngữ cảnh cho AI."""
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
    """Lấy API key từ biến môi trường (OXION_API_KEY / GEMINI_API_KEY), st.secrets hoặc session_state."""
    for env_name in ("OXION_API_KEY", "GEMINI_API_KEY"):
        val = os.getenv(env_name, "").strip()
        if val:
            return val
    try:
        for secret_name in ("OXION_API_KEY", "GEMINI_API_KEY"):
            val = str(st.secrets.get(secret_name, "")).strip()
            if val:
                return val
    except Exception:
        pass
    return str(st.session_state.get("ai_api_key_input", "")).strip()


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_oxion_models(api_key: str) -> list[str]:
    """Tự động lấy danh sách model khả dụng từ Oxion AI (/v1/models)."""
    req = urllib.request.Request(
        f"{OXION_BASE_URL}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        models = [item["id"] for item in payload.get("data", []) if "id" in item]
        return sorted(models)
    except Exception:
        return []


def _call_oxion_chat(
    api_key: str,
    model_name: str,
    system_instruction: str,
    history: list[dict[str, str]],
    prompt_with_context: str,
) -> str:
    """Gọi endpoint OpenAI-compatible của Oxion AI (/v1/chat/completions)."""
    messages: list[dict[str, str]] = [{"role": "system", "content": system_instruction}]
    for msg in history[:-1]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt_with_context})

    body = json.dumps({"model": model_name, "messages": messages}).encode("utf-8")
    req = urllib.request.Request(
        f"{OXION_BASE_URL}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {err.code} từ Oxion AI: {detail}") from err


def render_ai_chatbot(df_filtered: pd.DataFrame, location: str = "main") -> None:
    """Hiển thị khung chat trợ lý phân tích dữ liệu B2B (hỗ trợ Google Gemini & Oxion AI)."""
    container = st.sidebar if location == "sidebar" else st

    container.subheader("🤖 Trợ lý AI Phân tích B2B (Gemini / Oxion AI)")
    container.caption(
        "Hỗ trợ cả Google Gemini API (`AIza...`) và Oxion AI Gateway (`cc_...` tại oxionai.com/v1)."
    )

    api_key = _resolve_api_key()
    entered_key = container.text_input(
        "Nhập API Key (Gemini `AIza...` hoặc Oxion `cc_...`)",
        value="",
        type="password",
        key="_input_ai_api_key",
        placeholder="cc_... hoặc AIza...",
        help="Không lưu cứng key trong code. Hỗ trợ biến môi trường OXION_API_KEY / GEMINI_API_KEY.",
    )
    if entered_key:
        st.session_state["ai_api_key_input"] = entered_key.strip()
        api_key = entered_key.strip()

    # Tự nhận diện nhà cung cấp từ tiền tố key
    detected_provider = "Oxion AI (oxionai.com/v1)" if api_key.startswith("cc_") else "Google Gemini API"
    provider = container.selectbox(
        "Nhà cung cấp API",
        options=["Google Gemini API", "Oxion AI (oxionai.com/v1)"],
        index=1 if detected_provider.startswith("Oxion") else 0,
    )

    selected_model = "gemini-3.8-flash"
    if provider.startswith("Oxion"):
        oxion_models = _fetch_oxion_models(api_key) if api_key.startswith("cc_") else []
        if oxion_models:
            selected_model = container.selectbox("Chọn Model trên Oxion AI", options=oxion_models)
        else:
            selected_model = container.text_input(
                "Tên Model trên Oxion AI",
                value="gemini-3.8-flash",
                help="Nhập mã model khả dụng trên tài khoản Oxion AI của bạn.",
            )

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
        reply = "⚠️ Vui lòng nhập API Key (Gemini `AIza...` hoặc Oxion `cc_...`) để sử dụng Chatbot."
        st.session_state["ai_chat_history"].append({"role": "assistant", "content": reply})
        with container.chat_message("assistant"):
            st.warning(reply)
        return

    data_context = build_dataframe_context(df_filtered)
    system_instruction = (
        "Bạn là Chuyên gia Phân tích Dữ liệu B2B cấp cao đang tư vấn cho Ban Giám đốc Superstore. "
        "Hãy trả lời hoàn toàn bằng tiếng Việt, ngắn gọn, súc tích, chỉ dựa trên số liệu thực tế trong "
        "ngữ cảnh được cung cấp, nêu rõ con số cụ thể (USD, %, chiết khấu) và đưa ra khuyến nghị hành động."
    )
    prompt_with_context = f"{data_context}\n\nCÂU HỎI CỦA GIÁM ĐỐC:\n{final_prompt}"

    with container.chat_message("assistant"):
        with st.spinner(f"{selected_model} đang phân tích dữ liệu..."):
            try:
                if provider.startswith("Oxion"):
                    reply = _call_oxion_chat(
                        api_key=api_key,
                        model_name=selected_model,
                        system_instruction=system_instruction,
                        history=st.session_state["ai_chat_history"],
                        prompt_with_context=prompt_with_context,
                    )
                else:
                    from google import genai

                    client = genai.Client(api_key=api_key)
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
                reply = f"❌ Lỗi khi gọi AI API ({provider}): {err}"
                st.error(reply)

    st.session_state["ai_chat_history"].append({"role": "assistant", "content": reply})
