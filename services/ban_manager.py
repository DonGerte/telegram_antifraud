"""Ban system with behavior fingerprinting."""
import hashlib
import logging
from typing import Optional, Dict
from services.memory import is_banned, get_recent_messages, record_message

logger = logging.getLogger("ban_manager")


def compute_fingerprint(user_id: int, message_type: str = "text") -> Optional[str]:
    """
    Compute a behavior fingerprint for a user.
    
    Fingerprint combines:
    - user_id
    - message patterns (frequency, type)
    - recent behavior
    """
    recent = get_recent_messages(user_id, window_seconds=3600)
    
    if not recent:
        return None
    
    # Extract patterns
    patterns = [m.get("text", "")[:20] for m in recent]  # First 20 chars of messages
    freq = len(recent)  # How many messages in last hour
    
    # Create fingerprint
    data = f"{user_id}:{message_type}:{freq}:{','.join(patterns)}"
    return hashlib.md5(data.encode()).hexdigest()


def is_user_banned(user_id: int) -> bool:
    """Check if user is banned (from memory)."""
    return is_banned(user_id)


def get_similar_fingerprints(fingerprint: str, threshold: float = 0.85) -> Dict:
    """
    Find users with similar fingerprints (multi-account detection).
    
    Returns dict of {user_id: similarity_score}
    """
    # This is a placeholder for multi-account detection
    # In production, you'd query a broader user database
    # For now, return empty dict (each bot run works independently)
    return {}


def detect_raid_pattern(chat_id: int, user_ids: list, time_window: int = 300) -> Dict:
    """
    Detect raid pattern: many new users in short time.
    
    Returns:
    {
        "is_raid": bool,
        "new_user_count": int,
        "pattern_score": float (0-1)
    }
    """
    # Placeholder for raid detection
    # Should check Redis/DB for join timestamps
    return {
        "is_raid": False,
        "new_user_count": 0,
        "pattern_score": 0.0
    }
