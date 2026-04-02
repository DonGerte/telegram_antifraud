import os
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from sqlalchemy import (create_engine, Column, Integer, String, Float,
                        DateTime, Text, select, inspect, text)
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/telegram_antifraud.db")

# Add SQLite optimization flags to avoid locking contention in local development.
# For production use PostgreSQL or a proper persistent DB.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        connect_args={
            "check_same_thread": False,
            "timeout": 30,
        },
        pool_pre_ping=True,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def is_db_available() -> bool:
    return engine is not None


class UserEvent(Base):
    __tablename__ = "user_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    chat_id = Column(Integer, index=True)
    signal = Column(String(64), index=True)
    value = Column(Float, default=0.0)
    ts = Column(DateTime, default=datetime.utcnow)
    raw_text = Column(Text, nullable=True)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    first_name = Column(String(128), nullable=True)
    username = Column(String(128), nullable=True)
    strikes = Column(Integer, default=0)
    banned = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Ban(Base):
    __tablename__ = "bans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    reason = Column(Text, nullable=True)
    banned_at = Column(DateTime, default=datetime.utcnow)
    banned_by_id = Column(Integer, nullable=True)  # Admin who banned
    banned_by_username = Column(String(128), nullable=True)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    chat_id = Column(Integer, index=True)
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    # Ensure new columns added safely for migrations from older schema
    try:
        insp = inspect(engine)
        if "bans" in insp.get_table_names():
            cols = [c["name"] for c in insp.get_columns("bans")]
            with engine.begin() as conn:
                if "banned_by_id" not in cols:
                    conn.execute(text("ALTER TABLE bans ADD COLUMN banned_by_id INTEGER"))
                if "banned_by_username" not in cols:
                    conn.execute(text("ALTER TABLE bans ADD COLUMN banned_by_username VARCHAR(128)"))
    except Exception as e:
        # If the schema is already correct or the DB is read-only, continue anyway
        print(f"WARNING: init_db migration check failed: {e}")


def create_event(event: Dict):
    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            with SessionLocal() as db:
                db_event = UserEvent(
                    user_id=event["user_id"],
                    chat_id=event["chat_id"],
                    signal=event["signal"],
                    value=event.get("value", 1.0),
                    ts=event.get("ts", datetime.utcnow()),
                    raw_text=event.get("raw_text"),
                )
                db.add(db_event)
                db.commit()
            return
        except Exception as e:
            if "database is locked" in str(e).lower() and attempt < attempts:
                time.sleep(1)
                continue
            raise


def get_events_by_user(user_id: int, from_ts: Optional[datetime] = None) -> List[Dict]:
    with SessionLocal() as db:
        query = select(UserEvent).where(UserEvent.user_id == user_id)
        if from_ts is not None:
            query = query.where(UserEvent.ts >= from_ts)
        results = db.execute(query).scalars().all()
        return [
            {
                "user_id": e.user_id,
                "chat_id": e.chat_id,
                "signal": e.signal,
                "value": e.value,
                "ts": e.ts,
                "raw_text": e.raw_text,
            }
            for e in results
        ]


def get_users_in_chat(chat_id: int, window_hours: int = 24) -> List[int]:
    with SessionLocal() as db:
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        query = select(UserEvent.user_id).where(UserEvent.chat_id == chat_id, UserEvent.ts >= cutoff).distinct()
        results = db.execute(query).scalars().all()
        return results
