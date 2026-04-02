"""User memory service - lightweight JSON-based persistence."""
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path("data")
STORE_FILE = DATA_DIR / "store.json"


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)


def load_store() -> Dict:
    """Load user data from JSON file."""
    ensure_data_dir()
    if STORE_FILE.exists():
        try:
            with open(STORE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"users": {}, "metadata": {}}
    return {"users": {}, "metadata": {}}


def save_store(data: Dict):
    """Save user data to JSON file."""
    ensure_data_dir()
    with open(STORE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_user(user_id: int) -> Optional[Dict]:
    """Get user record from memory."""
    store = load_store()
    user_key = str(user_id)
    return store.get("users", {}).get(user_key)


def record_message(user_id: int, text: str, chat_id: int, timestamp: Optional[float] = None):
    """Record a message for a user."""
    if timestamp is None:
        timestamp = time.time()
    
    store = load_store()
    user_key = str(user_id)
    
    if user_key not in store["users"]:
        store["users"][user_key] = {
            "user_id": user_id,
            "messages": [],
            "strikes": 0,
            "banned": False,
            "first_seen": timestamp,
            "last_seen": timestamp
        }
    
    user = store["users"][user_key]
    user["messages"].append({
        "text": text,
        "chat_id": chat_id,
        "timestamp": timestamp
    })
    
    # Keep only last 50 messages in memory
    if len(user["messages"]) > 50:
        user["messages"] = user["messages"][-50:]
    
    user["last_seen"] = timestamp
    save_store(store)


def get_recent_messages(user_id: int, window_seconds: int = 3600) -> List[Dict]:
    """Get user messages in the last N seconds."""
    user = get_user(user_id)
    if not user or not user.get("messages"):
        return []
    
    cutoff = time.time() - window_seconds
    return [m for m in user["messages"] if m["timestamp"] > cutoff]


def add_strike(user_id: int) -> int:
    """Add a strike to user. Returns new strike count."""
    store = load_store()
    user_key = str(user_id)
    
    if user_key not in store["users"]:
        store["users"][user_key] = {
            "user_id": user_id,
            "messages": [],
            "strikes": 1,
            "banned": False,
            "first_seen": time.time(),
            "last_seen": time.time()
        }
    else:
        store["users"][user_key]["strikes"] += 1
    
    save_store(store)
    return store["users"][user_key]["strikes"]


def get_strikes(user_id: int) -> int:
    """Get strike count for user."""
    user = get_user(user_id)
    return user.get("strikes", 0) if user else 0


def ban_user(user_id: int, reason: str = "", banned_by_id: int = None, banned_by_username: str = None):
    """Ban a user."""
    store = load_store()
    user_key = str(user_id)
    
    if user_key not in store["users"]:
        store["users"][user_key] = {
            "user_id": user_id,
            "messages": [],
            "strikes": 3,
            "banned": True,
            "ban_reason": reason,
            "ban_time": time.time(),
            "banned_by_id": banned_by_id,
            "banned_by_username": banned_by_username,
            "first_seen": time.time(),
            "last_seen": time.time()
        }
    else:
        store["users"][user_key]["banned"] = True
        store["users"][user_key]["ban_reason"] = reason
        store["users"][user_key]["ban_time"] = time.time()
        store["users"][user_key]["banned_by_id"] = banned_by_id
        store["users"][user_key]["banned_by_username"] = banned_by_username
    
    save_store(store)


def unban_user(user_id: int) -> bool:
    """Unban a user."""
    store = load_store()
    user_key = str(user_id)
    
    if user_key in store["users"]:
        store["users"][user_key]["banned"] = False
        store["users"][user_key].pop("ban_reason", None)
        store["users"][user_key].pop("ban_time", None)
        save_store(store)
        return True
    return False


def is_banned(user_id: int) -> bool:
    """Check if user is banned."""
    user = get_user(user_id)
    return user.get("banned", False) if user else False


def clear_strikes(user_id: int):
    """Clear strikes for a user (e.g., after timeout period)."""
    store = load_store()
    user_key = str(user_id)
    
    if user_key in store["users"]:
        store["users"][user_key]["strikes"] = 0
        save_store(store)


def get_user_profile(user_id: int) -> Optional[Dict]:
    """Get full user profile for analysis."""
    user = get_user(user_id)
    if not user:
        return None
    
    return {
        "user_id": user.get("user_id"),
        "strikes": user.get("strikes", 0),
        "banned": user.get("banned", False),
        "first_seen": user.get("first_seen"),
        "last_seen": user.get("last_seen"),
        "message_count": len(user.get("messages", [])),
        "ban_reason": user.get("ban_reason", "")
    }
