from collections import defaultdict

try:
    import redis
except ImportError:
    redis = None
import json

import config

# grafos simplificados para operadores
clusters = defaultdict(set)

_redis = None
if redis and config.REDIS_URL:
    try:
        _redis = redis.from_url(config.REDIS_URL)
    except Exception:
        _redis = None


def add_edge(uid1: int, uid2: int):
    clusters[uid1].add(uid2)
    clusters[uid2].add(uid1)
    if _redis:
        try:
            # mantenemos una set por usuario en Redis
            _redis.sadd(f"cluster:{uid1}", uid2)
            _redis.sadd(f"cluster:{uid2}", uid1)
        except Exception:
            pass


def get_cluster(uid: int):
    seen = set()
    stack = [uid]

    # optionally hydrate from Redis
    if _redis:
        try:
            members = _redis.smembers(f"cluster:{uid}")
            for m in members:
                clusters[uid].add(int(m))
        except Exception:
            pass

    while stack:
        u = stack.pop()
        if u in seen:
            continue
        seen.add(u)
        stack.extend(clusters[u] - seen)
    return seen
