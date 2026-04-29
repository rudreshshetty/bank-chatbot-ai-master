import streamlit as st

# ================== PAGE CONFIG (ONLY ONCE) ==================
st.set_page_config(
    page_title="BankBot",
    layout="wide",
    page_icon="🏦"
)

# ================== SESSION STATE ==================
if "page" not in st.session_state:
    st.session_state.page = "welcome"

if "username" not in st.session_state:
    st.session_state.username = "Teja"

if "chat" not in st.session_state:
    st.session_state.chat = []

# ================== WELCOME PAGE ==================
def welcome_page():
    st.markdown(
        """
        <h1 style='text-align:center;'>Welcome 👋</h1>
        <h3 style='text-align:center;'>Professional Banking Chatbot System</h3>
        <p style='text-align:center;'>Secure • Reliable • Smart Banking Assistant</p>
        <br><br>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🚀 Continue to Banking Dashboard"):
            st.session_state.page = "dashboard"
            st.experimental_rerun()

# ================== DASHBOARD PAGE ==================
def dashboard_page():

    # ---------- SIDEBAR ----------
    st.sidebar.title("🏦 BankBot Menu")

    service = st.sidebar.radio(
        "Select Service",
        ["None", "Check Balance", "Transactions", "Loans", "ATM Info"],
        index=0
    )

    if st.sidebar.button("🆕 New Chat"):
        st.session_state.chat = []
        st.experimental_rerun()

    # ---------- MAIN HEADER ----------
    st.header(f"Welcome {st.session_state.username} 👋")

    # ---------- SERVICE DISPLAY ----------
    if service == "Check Balance":
        st.success("💰 Your current balance is ₹50,000")

    elif service == "Transactions":
        st.info("📑 Last transaction: ₹2,500 debited")

    elif service == "Loans":
        st.warning("🏦 Active Loan: ₹1,50,000 @ 11% interest")

    elif service == "ATM Info":
        st.success("📍 Nearest ATM: Main Road, Bangalore")

    # ---------- CHAT HISTORY ----------
    st.markdown("### 💬 Banking Conversation")

    for role, message in st.session_state.chat:
        if role == "user":
            st.markdown(f"🧑 **You:** {message}")
        else:
            st.markdown(f"🏦 **BankBot:** {message}")

    # ---------- USER INPUT ----------
    user_input = st.text_input(
        "Ask a banking question",
        placeholder="Example: balance, loan details, ATM location"
    )

    if user_input:
        q = user_input.lower().strip()
        st.session_state.chat.append(("user", user_input))

        # ---------- GREETINGS ----------
        if q in ["hi", "hello", "hey", "good morning", "good evening"]:
            reply = (
                "👋 Hello! I’m your professional banking assistant.\n\n"
                "You can ask about **balance, transactions, loans, or ATM info**."
            )

        # ---------- BANKING QUESTIONS ----------
        elif any(word in q for word in ["balance", "account"]):
            reply = "💰 Your current balance is ₹50,000"

        elif any(word in q for word in ["transaction", "debit", "credit"]):
            reply = "📑 Recent transaction: ₹2,500 debited"

        elif "loan" in q:
            reply = "🏦 Active loan: ₹1,50,000 at 11% annual interest"

        elif "atm" in q:
            reply = "📍 Nearest ATM: Main Road, Bangalore"

        # ---------- NON-BANKING ----------
        else:
            reply = (
                "❌ This is a **professional banking system**.\n\n"
                "Please ask **banking-related questions only**."
            )

        st.session_state.chat.append(("bot", reply))
        st.experimental_rerun()

# ================== PAGE ROUTER ==================
if st.session_state.page == "welcome":
    welcome_page()

elif st.session_state.page == "dashboard":
    dashboard_page()
