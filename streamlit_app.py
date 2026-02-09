import streamlit as st
import tiktoken
from main import ask_guruji  # simplified Guruji brain

# ---------------- TOKEN UTILS ----------------
encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(encoding.encode(text))


# ---------------- AZURE PRICING (per 1M tokens) ----------------
INPUT_COST_PER_1M = 0.25
OUTPUT_COST_PER_1M = 2.00


# ---------------- STREAMLIT CONFIG ----------------
st.set_page_config(page_title="AIGuruji", layout="centered")
st.title("🙏 AIGuruji – Mantra Guide")


# ---------------- SESSION STATE ----------------
if "history" not in st.session_state:
    st.session_state.history = []

if "costs" not in st.session_state:
    st.session_state.costs = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_cost": 0.0
    }


# ---------------- INPUT ----------------
user_input = st.text_input("Ask your question:")


# ---------------- ACTION ----------------
if st.button("Ask") and user_input.strip():
    # 🔮 Call Guruji (SINGLE TURN)
    reply = ask_guruji(user_input)

    # -------- TOKEN ESTIMATION --------
    input_tokens = count_tokens(user_input)
    output_tokens = count_tokens(reply)

    input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_1M
    output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_1M
    turn_cost = input_cost + output_cost

    # -------- UPDATE TOTALS --------
    st.session_state.costs["input_tokens"] += input_tokens
    st.session_state.costs["output_tokens"] += output_tokens
    st.session_state.costs["total_cost"] += turn_cost

    # -------- UPDATE CHAT HISTORY (UI ONLY) --------
    st.session_state.history.append(("user", user_input))
    st.session_state.history.append(("assistant", reply))


# ---------------- CHAT DISPLAY ----------------
for role, message in st.session_state.history:
    with st.chat_message(role):
        st.write(message)


# ---------------- COST BREAKDOWN ----------------
st.divider()
st.subheader("📊 Token & Cost Breakdown")

st.write(f"🟦 **Input tokens:** {st.session_state.costs['input_tokens']}")
st.write(f"🟨 **Output tokens:** {st.session_state.costs['output_tokens']}")
st.write(f"💰 **Estimated total cost:** ${st.session_state.costs['total_cost']:.6f}")

st.caption("ℹ️ Costs are per-turn estimates. History is NOT sent to the model.")


# ---------------- CLEAR CHAT ----------------
if st.button("Clear Chat"):
    st.session_state.history = []
    st.session_state.costs = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_cost": 0.0
    }
    st.experimental_rerun()
