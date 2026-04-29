# bank_app.py

import streamlit as st
import sqlite3
import bcrypt
import json
import requests
from datetime import datetime

# --- Configuration ---
DB_NAME = 'bank_chatbot.db'
OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'llama3' # Change this to your model name

# --- Database Helpers ---
def get_db_connection():
    return sqlite3.connect(DB_NAME)

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# --- Ollama / AI Logic ---

# In a real RAG setup, this context would be retrieved from a vector database.
# For simplicity, we hardcode banking knowledge here.
BANKING_KNOWLEDGE = (
    "A standard transaction fee is $1.00. "
    "The maximum daily ATM withdrawal limit is $500. "
    "Loan interest rates start at 4.5%. "
    "Overdraft fees are $35. "
)

def generate_ollama_response(user_prompt, chat_history):
    # This acts as your RAG/Guardrail logic
    system_prompt = (
        "You are a helpful and secure bank chatbot. "
        "Your current knowledge base is: " + BANKING_KNOWLEDGE + " "
        "Answer the user's question based on your banking knowledge and previous conversation. "
        "If the question is completely unrelated to banking, respond strictly with: 'I can only assist with bank-related inquiries, such as transactions, accounts, and loan information.' "
    )
    
    # Simple history formatting (Ollama expects a list of messages)
    history_messages = [
        {"role": "system", "content": system_prompt},
        # Add past messages
        *[{"role": msg['role'], "content": msg['content']} for msg in chat_history],
        {"role": "user", "content": user_prompt}
    ]

    payload = {
        "model": OLLAMA_MODEL,
        "messages": history_messages,
        "stream": False # Set to True if you want streaming response
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()['message']['content']
    except requests.exceptions.RequestException as e:
        return f"Sorry, the AI service is unavailable. Error: {e}"

# --- Chat History Management ---

def save_chat_session(user_id, topic, messages):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Convert list of messages to JSON string for storage
    messages_json = json.dumps(messages)
    
    cursor.execute(
        "INSERT INTO chat_history (user_id, topic, messages) VALUES (?, ?, ?)",
        (user_id, topic, messages_json)
    )
    conn.commit()
    conn.close()

def load_chat_sessions(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, topic, messages FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC", 
        (user_id,)
    )
    sessions = []
    for row in cursor.fetchall():
        # Convert messages from JSON string back to list
        try:
            messages = json.loads(row[2])
        except (json.JSONDecodeError, TypeError):
            messages = []
            
        sessions.append({
            'id': row[0],
            'topic': row[1],
            'messages': messages
        })
    conn.close()
    return sessions
# bank_app.py (continued)

# --- Session State Initialization ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
# Stores the current chat conversation
if "messages" not in st.session_state:
    st.session_state["messages"] = []
# Stores the current chat name for saving
if "current_chat_topic" not in st.session_state:
    st.session_state["current_chat_topic"] = "New Banking Chat"
# Controls the main view (Dashboard vs. Banking Activities)
if "current_view" not in st.session_state:
    st.session_state["current_view"] = "Dashboard"

# --- Authentication Pages ---

def register_page():
    st.title("🏦 Bank Chatbot Registration")
    
    with st.form("register_form"):
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
                    # Initialize default account data
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

def login_page():
    st.title("🔑 Bank Chatbot Login")

    with st.form("login_form"):
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
                    st.session_state["current_view"] = "Dashboard"
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")
            else:
                st.error("Incorrect username or password.")
                
# --- Banking Activities Pages ---

def show_balance():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE user_id = ?", (st.session_state["user_id"],))
    balance = cursor.fetchone()[0]
    conn.close()
    
    st.subheader("💰 Account Balance")
    st.metric(label="Current Balance", value=f"${balance:,.2f}")
    
def show_loan_info():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT loan_status FROM accounts WHERE user_id = ?", (st.session_state["user_id"],))
    loan_status = cursor.fetchone()[0]
    conn.close()
    
    st.subheader("🏦 Loan Information")
    st.info(f"Your current loan status: **{loan_status}**")
    st.caption("Apply for a loan by talking to the AI chat above.")

# Placeholder for other activities
def show_atm_info():
    st.subheader("📍 ATM Information")
    st.write("Closest ATM: 123 Main St (Open 24/7).")
    st.caption("Daily withdrawal limit is $500.")

def show_transaction():
    st.subheader("💸 Transactions")
    # In a real app, this would query a transactions table
    st.dataframe([
        {"Date": "2024-12-01", "Type": "Deposit", "Amount": "+$500.00"},
        {"Date": "2024-12-03", "Type": "ATM Withdrawal", "Amount": "-$100.00"},
    ])
    
# --- Main Chatbot Interface ---
def chatbot_interface():
    st.title(f"💬 Bank Chatbot: {st.session_state['current_chat_topic']}")
    
    # 1. Display Chat History
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 2. Handle User Input
    if prompt := st.chat_input("Ask about your account, transactions, or banking services..."):
        # Add user message to history
        st.session_state["messages"].append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Pass *full* history to Ollama for context
                full_history = st.session_state["messages"] 
                response = generate_ollama_response(prompt, full_history) 
            
            st.markdown(response)
            
            # Add AI message to history
            st.session_state["messages"].append({"role": "assistant", "content": response})

# --- Sidebar and Main Dashboard ---

def main_dashboard():
    st.sidebar.title(f"Welcome, {st.session_state['username']}")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear() or st.rerun())

    # Sidebar Navigation for Banking Activities
    st.sidebar.header("🏦 Banking Activities")
    activity_map = {
        "Balance": show_balance, 
        "Loan Information": show_loan_info, 
        "ATM Information": show_atm_info, 
        "Transactions": show_transaction
    }

    # Use Streamlit radio for single selection
    selected_activity = st.sidebar.radio("Select an Activity:", list(activity_map.keys()), index=0)
    
    # Banking Activity Display
    activity_map[selected_activity]()

    st.markdown("---")
    
    # Main Chatbot Area
    chatbot_interface()
    
    # AI Platform / Chat History Sidebar
    st.sidebar.header("🧠 AI Tools & History")
    
    # "New Chat" button logic (Saves current chat and starts a new one)
    if st.sidebar.button("➕ New Banking Chat"):
        if st.session_state["messages"]:
            # 1. Save the existing chat before starting a new one
            save_chat_session(
                st.session_state["user_id"], 
                st.session_state["current_chat_topic"], 
                st.session_state["messages"]
            )
            
        # 2. Reset session state for a new chat
        st.session_state["messages"] = []
        st.session_state["current_chat_topic"] = f"New Banking Chat ({datetime.now().strftime('%H:%M')})"
        st.rerun()
    
    # History Loading
    st.sidebar.subheader("Past Conversations")
    
    chat_sessions = load_chat_sessions(st.session_state["user_id"])
    
    for session in chat_sessions:
        # Button to load a past session
        if st.sidebar.button(f"🗓️ {session['topic']}", key=f"session_{session['id']}"):
            # Load the selected chat session
            st.session_state["messages"] = session['messages']
            st.session_state["current_chat_topic"] = session['topic']
            st.rerun()


# --- Main Application Loop ---

def main():
    st.set_page_config(page_title="Bank Chatbot AI", layout="wide")

    if st.session_state["logged_in"]:
        main_dashboard()
    else:
        # Simple tab interface for Login/Register
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            login_page()
        with tab2:
            register_page()

if __name__ == '__main__':
    main()