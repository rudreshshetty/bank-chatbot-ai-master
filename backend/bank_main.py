# bank_app.py (Final Corrected Version)

import streamlit as st
import sqlite3
import bcrypt
import json
from datetime import datetime
import re 
LLM_MODEL = "gemma3:4b"
# --- Configuration ---
DB_NAME = 'bank_chatbot.db'

# --- Database Helpers ---
def get_db_connection():
    return sqlite3.connect(DB_NAME)

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# --- Chat History Management ---

def save_chat_session(user_id, topic, messages):
    if not messages:
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    messages_json = json.dumps(messages)
    
    if 'session_id' in st.session_state and st.session_state["session_id"] is not None:
        cursor.execute(
            "UPDATE chat_history SET topic = ?, messages = ?, timestamp = CURRENT_TIMESTAMP WHERE id = ?",
            (topic, messages_json, st.session_state["session_id"])
        )
    else:
        cursor.execute(
            "INSERT INTO chat_history (user_id, topic, messages) VALUES (?, ?, ?)",
            (user_id, topic, messages_json)
        )
        st.session_state["session_id"] = cursor.lastrowid

    conn.commit()
    conn.close()

def load_chat_sessions(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, topic, messages, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC", 
        (user_id,)
    )
    sessions = []
    for row in cursor.fetchall():
        try:
            messages = json.loads(row[2])
        except (json.JSONDecodeError, TypeError):
            messages = []
            
        sessions.append({
            'id': row[0],
            'topic': row[1],
            'messages': messages,
            'timestamp': row[3]
        })
    conn.close()
    return sessions

def delete_chat_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    
    if st.session_state.get("session_id") == session_id:
        st.session_state["messages"] = []
        st.session_state["current_chat_topic"] = "New Banking Chat"
        st.session_state["session_id"] = None
        
    st.success(f"Chat session deleted.")
    st.rerun()

# --- MOCK AI / Guardrail Logic (STRICTLY ENFORCED) ---

def generate_ollama_response(user_prompt, chat_history):
    user_prompt_lower = user_prompt.lower()
    
    banking_keywords = ["balance", "money", "loan", "interest", "atm", "limit", "fee", "overdraft", "account", "transaction", "bank", "deposit", "withdraw"]

    if any(word in user_prompt_lower for word in ["hello", "hi", "hey"]):
        return "Hello! I am your Bank Chatbot AI. I can assist you with banking inquiries regarding accounts, loans, and services. How can I help you?"
    
    if any(keyword in user_prompt_lower for keyword in banking_keywords):
        
        if "balance" in user_prompt_lower or "account" in user_prompt_lower:
            return "For your real-time balance, please use the **'Balance' button** under Banking Activities, as I cannot access specific account numbers directly for security reasons."
        elif "loan" in user_prompt_lower or "interest" in user_prompt_lower:
            return "Our current standard loan interest rates start at 4.5%. For a personalized quote, please click the **'Loan Information'** button."
        elif "fee" in user_prompt_lower or "overdraft" in user_prompt_lower:
            return "A standard transaction fee is $1.00, and the overdraft fee is $35."
        elif "atm" in user_prompt_lower or "limit" in user_prompt_lower:
            return "The maximum daily ATM withdrawal limit is $500. You can find nearest locations under **'ATM Information'**."
        else:
            return "Thank you for your banking query. Please be more specific about the service you are looking for (e.g., balance, loan details, fees)."
    
    return "I can only assist with bank-related inquiries, such as transactions, accounts, and loan information. I cannot answer general questions."

def generate_topic_name(prompt):
    words = prompt.split()[:5]
    topic = " ".join(words).replace('.', '').replace('?', '').strip()
    return topic if len(topic) > 0 else "Untitled Chat"

# --- Session State Initialization ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "username" not in st.session_state: st.session_state["username"] = None
if "user_id" not in st.session_state: st.session_state["user_id"] = None
if "messages" not in st.session_state: st.session_state["messages"] = []
if "current_chat_topic" not in st.session_state: st.session_state["current_chat_topic"] = "New Banking Chat"
if "session_id" not in st.session_state: st.session_state["session_id"] = None
if "current_view" not in st.session_state: st.session_state["current_view"] = "Chatbot" # Default view is Chatbot

# --- Banking Activities Pages ---

def show_balance():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE user_id = ?", (st.session_state["user_id"],))
    balance = cursor.fetchone()[0]
    conn.close()
    
    st.header("💰 Account Balance")
    st.info("This section shows your real-time account data.")
    st.metric(label="Current Available Balance", value=f"${balance:,.2f}", delta="Up-to-Date")
    
def show_loan_info():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT loan_status FROM accounts WHERE user_id = ?", (st.session_state["user_id"],))
    loan_status = cursor.fetchone()[0]
    conn.close()
    
    st.header("🏦 Loan Information")
    st.info("Manage your existing loans or inquire about new applications.")
    st.markdown(f"**Current Loan Status:** `{loan_status}`")
    st.caption("Contact the AI Chatbot for details on interest rates.")

def show_atm_info():
    st.header("📍 ATM & Branch Information")
    st.info("Find nearest locations and withdrawal limits.")
    st.write("Closest ATM: **123 Main St, Financial District**")
    st.write("Nearest Branch: **456 Elm Ave, Downtown**")
    st.caption("Daily ATM withdrawal limit: **$500**.")

def show_transaction():
    st.header("💸 Transaction History")
    st.info("Review your recent account activity.")
    st.dataframe(
        [
            {"Date": "2024-12-05", "Description": "Salary Deposit", "Amount": "+$2,500.00"},
            {"Date": "2024-12-04", "Description": "Online Purchase (Amazon)", "Amount": "-$45.99"},
            {"Date": "2024-12-03", "Description": "ATM Withdrawal", "Amount": "-$100.00"},
        ], 
        use_container_width=True
    )

# --- Main Chatbot Interface ---
def chatbot_interface():
    st.header(f"💬 Chatbot: {st.session_state['current_chat_topic']}")
    st.caption("Ask questions about banking products or policies.")
    
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about your account or banking services..."):
        if st.session_state["current_chat_topic"] == "New Banking Chat":
            st.session_state["current_chat_topic"] = generate_topic_name(prompt)
        
        st.session_state["messages"].append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                full_history = st.session_state["messages"] 
                response = generate_ollama_response(prompt, full_history) 
            
            st.markdown(response)
            
            st.session_state["messages"].append({"role": "assistant", "content": response})
            
            save_chat_session(
                st.session_state["user_id"], 
                st.session_state["current_chat_topic"], 
                st.session_state["messages"]
            )
            st.rerun() 


# --- Sidebar and Main Dashboard (CORRECTED Button Logic) ---

def main_dashboard():
    st.set_page_config(page_title="Bank Chatbot AI", layout="wide")
    
    with st.sidebar:
        st.title(f"💳 Welcome, {st.session_state['username']}")
        st.button("Exit / Logout", on_click=lambda: st.session_state.clear() or st.rerun(), type="primary")
        
        st.markdown("---")
        
        # 1. Banking Activities Navigation
        st.header("🏦 Banking Activities")
        
        activity_map = {
            "Balance": show_balance, 
            "Loan Information": show_loan_info, 
            "ATM Information": show_atm_info, 
            "Transactions": show_transaction
        }
        
        # Display the activity buttons
        for activity_name in activity_map.keys():
            # CORRECTED LOGIC: Only pass type="secondary" if active. Omit type for default styling.
            if st.session_state["current_view"] == activity_name:
                button_clicked = st.button(
                    activity_name, 
                    use_container_width=True, 
                    type="secondary", # Active button uses secondary type
                    key=f"nav_{activity_name}"
                )
            else:
                button_clicked = st.button(
                    activity_name, 
                    use_container_width=True, 
                    key=f"nav_{activity_name}" # Inactive button omits the type argument
                )
                
            if button_clicked:
                st.session_state["current_view"] = activity_name
                st.rerun()

        st.markdown("---")
        
        # 2. AI Chat / History Management
        st.header("🧠 AI Tools & History")
        
        # New Chat button logic - Highlight if Chatbot view is active but no specific session is loaded
        chat_active = st.session_state["current_view"] == "Chatbot" and st.session_state["session_id"] is None
        
        if st.button("➕ Start New Chat", 
                     use_container_width=True, 
                     type="secondary" if chat_active else "primary"): 
            
            if st.session_state["messages"]:
                save_chat_session(
                    st.session_state["user_id"], 
                    st.session_state["current_chat_topic"], 
                    st.session_state["messages"]
                )
            st.session_state["messages"] = []
            st.session_state["current_chat_topic"] = "New Banking Chat"
            st.session_state["session_id"] = None
            st.session_state["current_view"] = "Chatbot" 
            st.rerun()

        st.subheader("Past Conversations")
        
        chat_sessions = load_chat_sessions(st.session_state["user_id"])
        
        if chat_sessions:
            for session in chat_sessions:
                col1, col2 = st.columns([4, 1])
                
                dt_obj = datetime.strptime(session['timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                display_time = dt_obj.strftime("%d %b, %I:%M %p")
                
                # Highlight the conversation if it is the current one
                is_current_session = st.session_state.get("session_id") == session['id'] and st.session_state["current_view"] == "Chatbot"

                if is_current_session:
                    button_clicked = col1.button(
                        f"**{session['topic']}**\n*{display_time}*", 
                        key=f"load_session_{session['id']}", 
                        use_container_width=True,
                        type="secondary" # Active button uses secondary type
                    )
                else:
                    button_clicked = col1.button(
                        f"**{session['topic']}**\n*{display_time}*", 
                        key=f"load_session_{session['id']}", 
                        use_container_width=True
                        # Omit type argument for default style
                    )

                if button_clicked:
                    st.session_state["messages"] = session['messages']
                    st.session_state["current_chat_topic"] = session['topic']
                    st.session_state["session_id"] = session['id']
                    st.session_state["current_view"] = "Chatbot" 
                    st.rerun()
                
                # Delete button (always default style, no need for type)
                col2.button(
                    "🗑️", 
                    key=f"del_session_{session['id']}", 
                    help="Delete conversation",
                    on_click=delete_chat_session,
                    args=(session['id'],)
                )

    # --- Main Content Area (Unified View) ---
    
    if st.session_state["current_view"] in activity_map:
        activity_map.get(st.session_state["current_view"])()
    else:
        # Default/Fallback is the Chatbot Interface
        chatbot_interface()


# --- Main Application Loop ---

def main():
    if st.session_state["logged_in"]:
        main_dashboard()
    else:
        st.set_page_config(page_title="Bank Chatbot AI", layout="centered")
        st.title("🏦 Secure Bank AI Access")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            login_page()
        with tab2:
            register_page()
            
def login_page():
    with st.form("login_form"):
        st.subheader("Sign In")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
            user_data = cursor.fetchone()
            conn.close()

            if user_data:
                user_id, hashed_pw = user_data
                if check_password(password, hashed_pw):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["user_id"] = user_id
                    st.session_state["current_view"] = "Chatbot" # Set default view to Chatbot
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")
            else:
                st.error("Incorrect username or password.")
                
def register_page():
    with st.form("register_form"):
        st.subheader("Create New Account")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        submit_button = st.form_submit_button("Register")

        if submit_button:
            if new_username and new_password:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    hashed_pw = hash_password(new_password)
                    cursor.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                        (new_username, hashed_pw)
                    )
                    conn.commit()
                    user_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO accounts (user_id, balance, loan_status) VALUES (?, ?, ?)",
                        (user_id, 1500.75, "None")
                    )
                    conn.commit()
                    st.success("Registration successful! Please log in.")
                except sqlite3.IntegrityError:
                    st.error("Username already exists.")
                finally:
                    conn.close()

if __name__ == '__main__':
    main()