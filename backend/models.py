from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


# -------------------- USER TABLE -------------------- #
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    accounts = relationship("Account", back_populates="user")
    loans = relationship("Loan", back_populates="user")


# -------------------- ACCOUNT TABLE -------------------- #
class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    account_number = Column(String, unique=True, nullable=False)
    balance = Column(Float, default=0.0)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="accounts")

    transactions = relationship("Transaction", back_populates="account")


# -------------------- TRANSACTION TABLE -------------------- #
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    type = Column(String)  # deposit / withdraw / transfer
    timestamp = Column(DateTime, default=datetime.utcnow)

    account_id = Column(Integer, ForeignKey("accounts.id"))
    account = relationship("Account", back_populates="transactions")


# -------------------- LOAN TABLE -------------------- #
class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True)
    loan_type = Column(String)
    amount = Column(Float)
    interest_rate = Column(Float)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="loans")
