import streamlit as st
import tiktoken
from main import ask_guruji  # Updated mantra brain

# ---------------- TOKEN UTILS ----------------
encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    if not text:
        return 0
    return len(encoding.encode(text))


# ---------------- AZURE COST ESTIMATE ----------------
INPUT_COST_PER_1M = 0.25
OUTPUT_COST_PER_1M = 2.00


# ---------------- STREAMLIT CONFIG ----------------
st.set_page_config(
    page_title="AIGuruji – Mantra Guide",
    layout="centered"
)

st.title("🙏 AIGuruji – Mantra Guide")
st.caption("A calm spiritual assistant that gently recommends mantras from sacred wisdom")


# ---------------- SESSION STATE ----------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "costs" not in st.session_state:
    st.session_state.costs = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_cost": 0.0
    }


# ---------------- USER INPUT ----------------
user_input = st.text_input(
    "Share what you are feeling or seeking:",
    placeholder="I feel anxious and restless..."
)


# ---------------- ASK BUTTON ----------------
if st.button("Ask") and user_input.strip():

    with st.spinner("🕉️ Finding a suitable mantra..."):
        reply = ask_guruji(user_input)

    # -------- TOKEN COUNT --------
    input_tokens = count_tokens(user_input)
    output_tokens = count_tokens(reply)

    input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_1M
    output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_1M
    turn_cost = input_cost + output_cost

    # -------- UPDATE COST TRACKING --------
    st.session_state.costs["input_tokens"] += input_tokens
    st.session_state.costs["output_tokens"] += output_tokens
    st.session_state.costs["total_cost"] += turn_cost

    # -------- UPDATE CHAT UI HISTORY --------
    st.session_state.chat_history.append(("user", user_input))
    st.session_state.chat_history.append(("assistant", reply))


# ---------------- CHAT DISPLAY ----------------
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)


# ---------------- COST DISPLAY ----------------
if st.session_state.chat_history:
    st.divider()
    st.subheader("📊 Token & Cost Breakdown")

    st.write(f"🟦 **Input tokens:** {st.session_state.costs['input_tokens']}")
    st.write(f"🟨 **Output tokens:** {st.session_state.costs['output_tokens']}")
    st.write(f"💰 **Estimated total cost:** `${st.session_state.costs['total_cost']:.6f}`")

    st.caption(
        "ℹ️ Cost is an approximate estimate per request. "
        "Conversation history is NOT sent to the model."
    )


# ---------------- CLEAR CHAT ----------------
if st.session_state.chat_history and st.button("Clear Chat"):
    st.session_state.chat_history = []
    st.session_state.costs = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_cost": 0.0
    }
    st.rerun()
