"""Database models for long-term audit trail and state management.

Uses SQLAlchemy ORM with PostgreSQL as backend.
Tables:
  - users: track user profiles, total scores, status
  - signals: all signals received with timestamp
  - actions: all mod actions (kick, mute, restrict) with reason
  - rules: current rule configurations (audit trail)
  - clips: audit clips of suspicious behavior
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost/telegram_antifraud")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    chat_ids = Column(String, default="")  # JSON list
    current_score = Column(Float, default=0.0)
    status = Column(String, default="normal")  # normal, restricted, banned
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    signals = relationship("Signal", back_populates="user")
    actions = relationship("ModAction", back_populates="user")


class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    signal_type = Column(String, index=True)  # link, honeypot, velocity, etc.
    value = Column(Float)
    chat_id = Column(Integer)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="signals")


class ModAction(Base):
    __tablename__ = "mod_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    action = Column(String)  # kick, mute, restrict, etc.
    chat_id = Column(Integer)
    reason = Column(String)
    rule_name = Column(String, nullable=True)
    score_at_action = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="actions")


class Rule(Base):
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    condition = Column(Text)  # JSON condition
    action = Column(String)
    reason = Column(String, nullable=True)
    priority = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    version = Column(Integer, default=1)  # audit trail
    created_by = Column(String, nullable=True)  # moderator
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)  # rule_created, rule_updated, user_banned, etc.
    actor = Column(String)  # moderator username
    target_user_id = Column(Integer, nullable=True)
    target_rule_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
