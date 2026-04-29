import streamlit as st

# Page config
st.set_page_config(
    page_title="BankBot – FAQ Assistant",
    page_icon="🏦",
    layout="wide"
)

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("🏦 BankBot")

    st.subheader("📁 Upload File")
    st.file_uploader(
        "Upload a file",
        type=["pdf", "txt", "jpg", "png", "jpeg"],
        accept_multiple_files=False
    )

    st.button("➕ New Chat")

    st.subheader("🎨 Theme")
    st.selectbox("Choose Theme", ["Modern Blue Banking"])

    st.markdown("---")
    st.write("Signed in as **Dharshini**")

    st.button("Change account")
    st.button("Logout")

# ---------- MAIN UI ----------
st.markdown(
    """
    <div style="
        background-color:#0a5bd3;
        padding:15px;
        border-radius:10px;
        text-align:center;
        color:white;
        font-size:26px;
        font-weight:bold;
        margin-bottom:20px;">
        BankBot — FAQ Assistant
    </div>
    """,
    unsafe_allow_html=True
)

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input box
user_input = st.chat_input("Type your message here")

if user_input:
    # Show user message
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )
    with st.chat_message("user"):
        st.write(user_input)

    # Placeholder bot response
    with st.chat_message("assistant"):
        st.write("Generating answer from Ollama...")

    st.session_state.messages.append(
        {"role": "assistant", "content": "Generating answer from Ollama..."}
    )
