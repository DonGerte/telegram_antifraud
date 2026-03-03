"""Utility to push dummy events into the Redis queue for testing."""
import json
import time

try:
    import redis
except ImportError:
    redis = None

import config

if __name__ == "__main__":
    if not redis:
        print("redis library not installed")
        exit(1)
    r = redis.from_url(config.REDIS_URL)
    # push a few messages and a join
    events = [
        {"type": "message", "uid": 111, "chat": -100, "ts": time.time(),
         "signal_type": "link", "value": 5, "raw": "http://spam"},
        {"type": "message", "uid": 112, "chat": -100, "ts": time.time(),
         "signal_type": "text", "value": 1, "raw": "hello"},
        {"type": "join", "chat": -100, "uid": 113, "ts": time.time()},
    ]
    for ev in events:
        r.rpush("data_bus", json.dumps(ev))
    print("pushed sample events")
