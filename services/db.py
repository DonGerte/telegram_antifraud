import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from sqlalchemy import (create_engine, Column, Integer, String, Float,
                        DateTime, Text, select)
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/telegram_antifraud.db")

engine = create_engine(DATABASE_URL, echo=False, future=True)
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


def init_db():
    Base.metadata.create_all(bind=engine)


def create_event(event: Dict):
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
