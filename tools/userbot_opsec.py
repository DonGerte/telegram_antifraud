"""Userbot session rotation and OPSEC utilities.

Handles rotating user sessions, managing proxy lists, and rate limiting
to avoid Telegram API bans or detection.
"""
import os
import json
import hashlib
import time
from pathlib import Path

SESSIONS_DIR = "sessions"
PROXIES_FILE = "proxies.json"


def initialize_sessions_dir():
    """Create sessions directory if it doesn't exist."""
    Path(SESSIONS_DIR).mkdir(exist_ok=True)


def create_session_name(api_id: int, user_id: int, variant: int = 0) -> str:
    """Generate a unique session name."""
    base = f"userbot_{api_id}_{user_id}"
    if variant > 0:
        base += f"_v{variant}"
    return base


def rotate_session(api_id: int, user_id: int, max_variants: int = 3):
    """Rotate to next session variant (useful for distributing load)."""
    for i in range(max_variants):
        session_name = create_session_name(api_id, user_id, i)
        session_path = os.path.join(SESSIONS_DIR, session_name)
        if not os.path.exists(session_path + ".session"):
            return session_name
    # If all exist, return the oldest (based on modification time)
    sessions = []
    for i in range(max_variants):
        sname = create_session_name(api_id, user_id, i)
        spath = os.path.join(SESSIONS_DIR, sname + ".session")
        if os.path.exists(spath):
            mtime = os.path.getmtime(spath)
            sessions.append((mtime, sname))
    if sessions:
        sessions.sort()
        return sessions[0][1]
    return create_session_name(api_id, user_id, 0)


def load_proxies(filename: str = PROXIES_FILE):
    """Load proxy list from JSON file."""
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data.get("proxies", [])
    except Exception:
        return []


def save_proxies(proxies: list, filename: str = PROXIES_FILE):
    """Save proxy list to JSON file."""
    with open(filename, 'w') as f:
        json.dump({"proxies": proxies}, f, indent=2)


def get_next_proxy(api_id: int, user_id: int):
    """Get next proxy in rotation for a user."""
    proxies = load_proxies()
    if not proxies:
        return None
    # Use hash of (api_id, user_id, timestamp) to vary selection
    idx = hash((api_id, user_id, int(time.time()) // 300)) % len(proxies)
    return proxies[idx]


class RateLimiter:
    """Simple rate limiter to avoid API throttling."""

    def __init__(self, max_calls: int = 30, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window = window_seconds
        self.calls = []

    def allow(self):
        """Check if action is allowed; returns True if within limit."""
        now = time.time()
        # Remove old calls
        self.calls = [t for t in self.calls if now - t < self.window]
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False

    def wait_if_needed(self):
        """Block until next call is allowed."""
        while not self.allow():
            time.sleep(0.1)


# Pre-configured rate limiters per action
limiters = {
    "get_messages": RateLimiter(20, 60),  # 20 msgs/min
    "forward_messages": RateLimiter(5, 60),  # 5 forwards/min
    "get_pinned_messages": RateLimiter(10, 60),  # 10 pins/min
}


def rate_limit(action: str):
    """Decorator to rate-limit a function call."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            limiter = limiters.get(action, RateLimiter())
            limiter.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper
    return decorator
