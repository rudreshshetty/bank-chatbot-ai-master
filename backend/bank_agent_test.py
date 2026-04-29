import os
import sys
from sqlalchemy import create_engine, text
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_ollama import ChatOllama
from langchain_community.agent_toolkits import create_sql_agent
# --- Configuration ---
# You confirmed that 'llama3' is installed.
LLM_MODEL = "llama3" 
DB_FILE = "bank_data.db"
# Ensure the Ollama server host is specified to avoid connection issues.
OLLAMA_HOST = "http://127.0.0.1:11434"

# --- STEP 1: Set up the Database and Data ---

# Clean up previous database file for a fresh start
if os.path.exists(DB_FILE):
    os.remove(DB_FILE) 

try:
    # Connect to the SQLite database file
    engine = create_engine(f"sqlite:///{DB_FILE}")

    # Create and populate the sample table
    with engine.connect() as connection:
        # Creating a simple schema for the LLM to understand
        connection.execute(text(
            """
            CREATE TABLE accounts (
                account_id INTEGER PRIMARY KEY,
                customer_name TEXT,
                balance REAL,
                account_type TEXT
            );
            """
        ))
        # Inserting banking data
        connection.execute(text(
            """
            INSERT INTO accounts (account_id, customer_name, balance, account_type) 
            VALUES 
            (101, 'Alice Smith', 1545.75, 'Checking'),
            (102, 'Bob Johnson', 8234.11, 'Savings'),
            (103, 'Charlie Brown', 50.00, 'Checking');
            """
        ))
        connection.commit()
    print(f"Database '{DB_FILE}' created and populated successfully.")

except Exception as e:
    print(f"Error during database setup: {e}")
    sys.exit(1)


# --- STEP 2: Initialize LangChain Components ---

try:
    # 1. Initialize the Ollama Model, explicitly setting the host
    llm = ChatOllama(model=LLM_MODEL, temperature=0, base_url=OLLAMA_HOST) 
    
    # Quick check to ensure LLM is accessible
    llm.invoke("Hello.") 
    print(f"Successfully connected to Ollama model: {LLM_MODEL}")

    # 2. Create the SQL Database utility object
    db = SQLDatabase(engine=engine)

    # 3. Create the Toolkit (provides the LLM tools like 'query_sql_db')
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    # --- STEP 3: Create the Text-to-SQL Agent ---
    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True, # Shows the LLM's thought process
        agent_type="openai-tools", 
        handle_parsing_errors=True
    )

except Exception as e:
    print(f"\n--- ERROR ---")
    print(f"Failed to initialize LLM or Agent. Is 'ollama serve' running?")
    print(f"Details: {e}")
    sys.exit(1)


# --- STEP 4: Run the Queries ---

print("\n" + "="*50)
print(f"Starting Agent Queries using model: {LLM_MODEL}")
print("="*50)

# Query 1: Find a specific balance
question1 = "What is the current balance for Alice Smith's account?"
print(f"User Query 1: {question1}")
response1 = agent_executor.invoke({"input": question1})
print(f"\nFinal Answer: {response1['output']}\n")

# Query 2: Perform an aggregation/calculation
question2 = "What is the total balance across all Checking accounts?"
print(f"User Query 2: {question2}")
response2 = agent_executor.invoke({"input": question2})
print(f"\nFinal Answer: {response2['output']}\n")