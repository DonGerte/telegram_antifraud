import time
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta

try:
    import redis
except ImportError:
    redis = None

import config
from services.user_history import get_user_events

# almacena señales por usuario en memoria
user_signals = defaultdict(list)

# si hay conexión, también almacenamos en Redis para persistencia
_redis = None
if redis and config.REDIS_URL:
    try:
        _redis = redis.from_url(config.REDIS_URL)
    except Exception:
        _redis = None

DECAY_LAMBDA = 0.1


def _decay(age_seconds: float) -> float:
    age_hours = age_seconds / 3600.0
    return math.exp(-DECAY_LAMBDA * age_hours)


def add_signal(uid: int, signal_type: str, value: float, chat: int, ts=None):
    """Añade una señal al usuario. Se guarda en memoria y opcionalmente en Redis."""
    ts = ts or time.time()
    entry = {"type": signal_type, "value": value, "chat": chat, "ts": ts}
    user_signals[uid].append(entry)
    if _redis:
        try:
            _redis.rpush(f"signals:{uid}", json.dumps(entry))
        except Exception:
            pass


def compute_score(uid: int, window_hours: int = 24):
    now = datetime.utcnow()
    window_start = now - timedelta(hours=window_hours)
    score = 0.0

    # events from resident cache (more recent) and stored history
    entries = user_signals.get(uid, [])

    # read Redis fallback
    if not entries and _redis:
        try:
            raw = _redis.lrange(f"signals:{uid}", 0, -1)
            if raw:
                entries = [json.loads(r) for r in raw]
                user_signals[uid] = entries
        except Exception:
            pass

    # include stored events from history
    history = get_user_events(uid, from_ts=window_start)
    for h in history:
        entries.append({
            "type": h.get("signal", "normal"),
            "value": h.get("value", 1.0),
            "chat": h.get("chat_id"),
            "ts": (h.get("ts").timestamp() if isinstance(h.get("ts"), datetime)
               else (datetime.fromisoformat(h.get("ts")).timestamp() if isinstance(h.get("ts"), str) else time.mktime(h.get("ts").timetuple()))),
        })

    for e in entries:
        age = time.time() - e["ts"]
        if age < 0:
            age = 0
        w = _decay(age)
        score += float(e.get("value", 1.0)) * w

    return min(score, 100.0)


if __name__ == "__main__":
    # demo simple
    add_signal(123, "link", 5, -100)
    print("score", compute_score(123))
