# create_professional_db.py
import sqlite3
from datetime import datetime

DB = "bank_professional.db"

def connect():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_tables(conn):
    cur = conn.cursor()

    # Branches
    cur.execute("""
    CREATE TABLE IF NOT EXISTS branches (
        branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        ifsc TEXT UNIQUE
    );
    """)

    # Customers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        dob TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Account types
    cur.execute("""
    CREATE TABLE IF NOT EXISTS account_types (
        type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        min_balance REAL DEFAULT 0,
        interest_rate REAL DEFAULT 0
    );
    """)

    # Accounts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        branch_id INTEGER,
        account_type_id INTEGER,
        account_no TEXT UNIQUE,
        balance REAL DEFAULT 0,
        opened_on TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Active',
        pin TEXT, -- simple PIN for demo only (hash in production)
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY(branch_id) REFERENCES branches(branch_id),
        FOREIGN KEY(account_type_id) REFERENCES account_types(type_id)
    );
    """)

    # ATM Cards
    cur.execute("""
    CREATE TABLE IF NOT EXISTS atm_cards (
        card_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL,
        card_no TEXT UNIQUE,
        cvv TEXT,
        expiry TEXT,
        status TEXT DEFAULT 'Active',
        pin TEXT,
        FOREIGN KEY(account_id) REFERENCES accounts(account_id)
    );
    """)

    # Loans
    cur.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL,
        loan_amount REAL NOT NULL,
        interest_rate REAL,
        term_months INTEGER,
        remaining_amount REAL,
        status TEXT DEFAULT 'Active',
        issued_on TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(account_id) REFERENCES accounts(account_id)
    );
    """)

    # Transactions (credit/debit)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL,
        txn_type TEXT NOT NULL, -- 'credit' or 'debit'
        amount REAL NOT NULL,
        balance_after REAL,
        narration TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(account_id) REFERENCES accounts(account_id)
    );
    """)

    # Fund transfers (from_account -> to_account)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fund_transfers (
        transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_account INTEGER NOT NULL,
        to_account INTEGER NOT NULL,
        amount REAL NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Completed',
        remark TEXT,
        FOREIGN KEY(from_account) REFERENCES accounts(account_id),
        FOREIGN KEY(to_account) REFERENCES accounts(account_id)
    );
    """)

    # Indexes for performance
    cur.execute("CREATE INDEX IF NOT EXISTS idx_accounts_customer ON accounts(customer_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_txn_account ON transactions(account_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_loans_account ON loans(account_id);")
    conn.commit()

def seed_demo(conn):
    cur = conn.cursor()

    # Check if already seeded
    cur.execute("SELECT COUNT(*) FROM customers")
    if cur.fetchone()[0] > 0:
        print("Demo data already present — skipping seed.")
        return

    # 1) Branch
    cur.execute("INSERT INTO branches (name, address, ifsc) VALUES (?, ?, ?)",
                ("Main Branch, Bengaluru", "MG Road, Bengaluru, India", "INFY0001234"))
    branch_id = cur.lastrowid

    # 2) Account types
    cur.execute("INSERT INTO account_types (name, min_balance, interest_rate) VALUES (?, ?, ?)",
                ("Savings", 1000.0, 3.5))
    savings_type = cur.lastrowid
    cur.execute("INSERT INTO account_types (name, min_balance, interest_rate) VALUES (?, ?, ?)",
                ("Current", 0.0, 0.0))
    current_type = cur.lastrowid

    # 3) Customers
    cur.execute("INSERT INTO customers (full_name, email, phone, dob) VALUES (?, ?, ?, ?)",
                ("Tejaswini R", "tejaswini@example.com", "9999999999", "1995-05-12"))
    cust1 = cur.lastrowid

    cur.execute("INSERT INTO customers (full_name, email, phone, dob) VALUES (?, ?, ?, ?)",
                ("Arjun K", "arjun@example.com", "9888888888", "1994-07-20"))
    cust2 = cur.lastrowid

    # 4) Accounts for customers
    # Account numbers are simple demo strings — in real systems use secure generation
    cur.execute("INSERT INTO accounts (customer_id, branch_id, account_type_id, account_no, balance, pin) VALUES (?, ?, ?, ?, ?, ?)",
                (cust1, branch_id, savings_type, "INFY0001001", 75000.0, "4321"))
    acc1 = cur.lastrowid

    cur.execute("INSERT INTO accounts (customer_id, branch_id, account_type_id, account_no, balance, pin) VALUES (?, ?, ?, ?, ?, ?)",
                (cust2, branch_id, savings_type, "INFY0001002", 25000.0, "1111"))
    acc2 = cur.lastrowid

    # 5) ATM card for acc1
    cur.execute("INSERT INTO atm_cards (account_id, card_no, cvv, expiry, pin) VALUES (?, ?, ?, ?, ?)",
                (acc1, "4111222233334444", "123", "2027-08", "4321"))

    # 6) Loan for acc1
    cur.execute("INSERT INTO loans (account_id, loan_amount, interest_rate, term_months, remaining_amount, status) VALUES (?, ?, ?, ?, ?, ?)",
                (acc1, 200000.0, 9.5, 60, 200000.0, "Active"))

    # 7) Transactions for accounts
    now = datetime.now().isoformat()
    txns = [
        (acc1, "credit", 50000.0, 75000.0, "Salary credited", now),
        (acc1, "debit", 2500.0, 72500.0, "Shopping - Mall", now),
        (acc2, "credit", 20000.0, 25000.0, "Salary credited", now),
        (acc2, "debit", 1500.0, 23500.0, "Grocery", now)
    ]
    cur.executemany("INSERT INTO transactions (account_id, txn_type, amount, balance_after, narration, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    txns)

    # 8) Example fund transfer (acc1 -> acc2)
    cur.execute("INSERT INTO fund_transfers (from_account, to_account, amount, remark) VALUES (?, ?, ?, ?)",
                (acc1, acc2, 5000.0, "Transfer to Arjun for rent"))
    # Update balances and insert transactions for the transfer
    # debit acc1
    cur.execute("UPDATE accounts SET balance = balance - ? WHERE account_id = ?", (5000.0, acc1))
    cur.execute("INSERT INTO transactions (account_id, txn_type, amount, balance_after, narration, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (acc1, "debit", 5000.0, 67500.0, "Transfer to INFY0001002", now))
    # credit acc2
    cur.execute("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (5000.0, acc2))
    cur.execute("INSERT INTO transactions (account_id, txn_type, amount, balance_after, narration, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (acc2, "credit", 5000.0, 28500.0, "Transfer from INFY0001001", now))

    conn.commit()
    print("Seeded demo data.")

def main():
    conn = connect()
    create_tables(conn)
    seed_demo(conn)
    conn.close()
    print("Database created:", DB)

if __name__ == "__main__":
    main()
