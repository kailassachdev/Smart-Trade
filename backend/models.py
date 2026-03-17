"""
models.py
---------
SQLAlchemy ORM models for Smart Trade.

ARCHITECTURAL IMPROVEMENTS:
- #1: Numeric type instead of Float for money columns (prevents floating-point drift)
- #3: `agent_enabled` column on User (persists agent state across server restarts)
- #5: `stop_loss_pct`, `max_allocation_pct` per-user risk rules stored on Wallet
- #8: `reason` column on Transaction (AI decision rationale persisted to DB, not just in-memory dict)
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Numeric, Text
from sqlalchemy.orm import relationship
from database import Base
import datetime


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)

    # IMPROVEMENT #3: persists agent on/off state so restarts don't silence the agent
    agent_enabled = Column(Boolean, default=False, nullable=False)

    wallet       = relationship("Wallet",      back_populates="user", uselist=False, cascade="all, delete-orphan")
    positions    = relationship("Position",    back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")


class Wallet(Base):
    __tablename__ = "wallets"

    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # IMPROVEMENT #1: Numeric(18, 6) prevents floating-point rounding errors on money values
    balance = Column(Numeric(18, 6), default=0.0, nullable=False)

    # IMPROVEMENT #5: Per-user risk configuration stored in the wallet row
    stop_loss_pct       = Column(Float, default=0.05)    # 5% stop-loss threshold
    max_allocation_pct  = Column(Float, default=0.20)    # 20% max single-stock allocation

    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="wallet")


class Position(Base):
    __tablename__ = "positions"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol        = Column(String(16), index=True, nullable=False)
    quantity      = Column(Integer, default=0, nullable=False)

    # IMPROVEMENT #1: Numeric for money
    average_price = Column(Numeric(18, 6), default=0.0, nullable=False)

    created_at    = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="positions")


class Transaction(Base):
    __tablename__ = "transactions"

    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol    = Column(String(16), nullable=False)
    action    = Column(String(16), nullable=False)  # BUY | SELL | DEPOSIT | WITHDRAW | SKIP_BUY | SKIP_SELL
    quantity  = Column(Integer, nullable=False)

    # IMPROVEMENT #1: Numeric for money
    price     = Column(Numeric(18, 6), nullable=False)

    # IMPROVEMENT #8: AI decision reason persisted to DB (not just in-memory dict)
    reason    = Column(Text, nullable=True)

    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="transactions")
