import time
import json
from collections import defaultdict

try:
    import redis
except ImportError:
    redis = None

import config

# almacena señales por usuario en memoria
user_signals = defaultdict(list)

# si hay conexión, también almacenamos en Redis para persistencia
_redis = None
if redis and config.REDIS_URL:
    try:
        _redis = redis.from_url(config.REDIS_URL)
    except Exception:
        _redis = None


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


def compute_score(uid: int):
    # si no hay señales en memoria, intentar cargar desde Redis
    entries = user_signals.get(uid, [])
    if not entries and _redis:
        try:
            raw = _redis.lrange(f"signals:{uid}", 0, -1)
            if raw:
                entries = [json.loads(r) for r in raw]
                user_signals[uid] = entries
        except Exception:
            pass

    score = 0.0
    decay = 0.99
    for e in entries:
        age = time.time() - e["ts"]
        weight = (decay ** (age / 3600))
        score += e["value"] * weight
    return score


if __name__ == "__main__":
    # demo simple
    add_signal(123, "link", 5, -100)
    print("score", compute_score(123))
