import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from services import db

STORE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "event_store.json")


def _read_store() -> Dict:
    try:
        with open(STORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"events": []}


def _write_store(data: Dict):
    os.makedirs(os.path.dirname(STORE_FILE), exist_ok=True)
    with open(STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, default=str, indent=2)


def record_event(user_id: int, chat_id: int, signal: str, value: float, ts: Optional[datetime] = None):
    ts = ts or datetime.utcnow()
    event = {
        "user_id": user_id,
        "chat_id": chat_id,
        "signal": signal,
        "value": float(value),
        "ts": ts.isoformat(),
    }

    # PostgreSQL/Mongo handler
    if db.is_db_available():
        db.create_event(event)
        return

    store = _read_store()
    store.setdefault("events", []).append(event)
    _write_store(store)


def get_user_events(user_id: int, from_ts: Optional[datetime] = None) -> List[Dict]:
    events: List[Dict] = []
    if db.is_db_available():
        events = db.get_events_by_user(user_id, from_ts)
        return events

    raw = _read_store().get("events", [])
    for e in raw:
        if e.get("user_id") != user_id:
            continue
        if from_ts:
            event_ts = datetime.fromisoformat(e.get("ts"))
            if event_ts < from_ts:
                continue
        structured = {
            "user_id": e["user_id"],
            "chat_id": e["chat_id"],
            "signal": e["signal"],
            "value": float(e["value"]),
            "ts": datetime.fromisoformat(e["ts"]),
        }
        events.append(structured)
    return events


def get_recent_events(window_minutes: int = 60) -> List[Dict]:
    threshold = datetime.utcnow() - timedelta(minutes=window_minutes)
    if db.is_db_available():
        with db.SessionLocal() as session:
            results = session.execute(
                "SELECT user_id, chat_id, signal, value, ts, raw_text FROM user_events WHERE ts >= :threshold",
                {"threshold": threshold},
            ).all()
        return [
            {
                "user_id": r[0],
                "chat_id": r[1],
                "signal": r[2],
                "value": r[3],
                "ts": r[4],
                "raw_text": r[5],
            }
            for r in results
        ]

    events = []
    raw = _read_store().get("events", [])
    for e in raw:
        event_ts = datetime.fromisoformat(e.get("ts"))
        if event_ts >= threshold:
            events.append({
                "user_id": e["user_id"],
                "chat_id": e["chat_id"],
                "signal": e["signal"],
                "value": float(e["value"]),
                "ts": event_ts,
            })
    return events
