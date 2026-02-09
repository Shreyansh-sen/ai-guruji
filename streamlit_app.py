import streamlit as st
import tiktoken

from main import ask_guruji  # mantra-only Guruji brain

# ---------------- TOKEN UTILS ----------------
encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    if not text:
        return 0
    return len(encoding.encode(text))


# ---------------- AZURE PRICING (per 1M tokens) ----------------
# NOTE: These are ESTIMATES, not exact Azure billing numbers
INPUT_COST_PER_1M = 0.25
OUTPUT_COST_PER_1M = 2.00


# ---------------- STREAMLIT CONFIG ----------------
st.set_page_config(
    page_title="AIGuruji – Mantra Guide",
    layout="centered"
)

st.title("🙏 AIGuruji – Mantra Guide")
st.caption("A calm spiritual assistant that gently recommends mantras")


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
user_input = st.text_input(
    "Ask what you are feeling or seeking:",
    placeholder="I feel anxious and restless..."
)


# ---------------- ACTION ----------------
if st.button("Ask") and user_input.strip():
    with st.spinner("🕉️ Finding a suitable mantra..."):
        # 🔮 SINGLE TURN CALL (no history sent)
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
        st.markdown(message)


# ---------------- COST BREAKDOWN ----------------
if st.session_state.history:
    st.divider()
    st.subheader("📊 Token & Cost Breakdown")

    st.write(f"🟦 **Input tokens:** {st.session_state.costs['input_tokens']}")
    st.write(f"🟨 **Output tokens:** {st.session_state.costs['output_tokens']}")
    st.write(f"💰 **Estimated total cost:** `${st.session_state.costs['total_cost']:.6f}`")

    st.caption(
        "ℹ️ Cost shown is an estimate per request. "
        "Conversation history is NOT sent to the model."
    )


# ---------------- CLEAR CHAT ----------------
if st.session_state.history and st.button("Clear Chat"):
    st.session_state.history = []
    st.session_state.costs = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_cost": 0.0
    }
    st.rerun()
