import logging
from datetime import datetime, timedelta
from collections import Counter

from sqlalchemy import text as sql_text
from services.user_history import get_user_events
from services.db import get_events_by_user

logger = logging.getLogger("correlator")


def detect_multi_group_user(user_id: int, min_groups: int = 2, window_hours: int = 24) -> bool:
    events = get_user_events(user_id, from_ts=datetime.utcnow() - timedelta(hours=window_hours))
    chat_ids = {e["chat_id"] for e in events}
    if len(chat_ids) >= min_groups:
        logger.info(f"User {user_id} active in multiple chats {chat_ids}")
        return True
    return False


def detect_campaign(trigger_window_seconds: int = 60, threshold: int = 3) -> bool:
    """Detect if many users send same phrase quickly."""
    now = datetime.utcnow()
    start = now - timedelta(seconds=trigger_window_seconds)
    # query raw DB not yet available in service
    # using user_history fallback can be slow
    # as placeholder, we inspect recent event store

    text_counter = Counter()
    # grab all users from last window by scanning DB through get_user_events for each unique user
    # O(n^2) but okay for MVP

    from services.db import SessionLocal, UserEvent
    with SessionLocal() as db:
        rows = db.execute(
            sql_text("SELECT user_id, raw_text FROM user_events WHERE ts >= :t"),
            {"t": start}
        ).all()
    for user_id, raw_text in rows:
        if not raw_text:
            continue
        normalized = raw_text.strip().lower()
        text_counter[normalized] += 1

    for phrase, count in text_counter.items():
        if count >= threshold:
            logger.warning(f"Campaign detected: '{phrase}' occurred {count} times in last {trigger_window_seconds}s")
            return True

    return False
