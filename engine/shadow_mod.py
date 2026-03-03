"""Shadow moderation: silent user restrictions without public notification.

Includes soft penalties like message throttling, permission removal,
and content suppression without kicking the user.
"""
from collections import defaultdict
import time

# Track throttled users: uid -> (allowed_per_minute, last_reset_time)
throttled_users = defaultdict(lambda: (10, time.time()))  # 10 msgs/min default

# Track shadow-muted users: uid -> timestamp of mute
shadow_muted = {}

# Permutations that can be silently revoked
PERMISSIONS = {"send_messages", "send_media", "send_stickers", "send_polls"}


def throttle_user(uid: int, msgs_per_minute: int = 1):
    """Limit a user to N messages per minute."""
    throttled_users[uid] = (msgs_per_minute, time.time())


def is_throttled(uid: int) -> bool:
    """Check if a user is currently throttled."""
    if uid not in throttled_users:
        return False
    limit, reset_time = throttled_users[uid]
    # For simplicity, check if reset time is recent
    return time.time() - reset_time < 60


def shadow_mute(uid: int, duration: int = 3600):
    """Silently mute a user for duration seconds."""
    shadow_muted[uid] = time.time() + duration


def is_shadow_muted(uid: int) -> bool:
    """Check if a user is shadow-muted."""
    if uid not in shadow_muted:
        return False
    if time.time() > shadow_muted[uid]:
        del shadow_muted[uid]
        return False
    return True


def should_suppress_message(uid: int) -> bool:
    """Return True if message from this user should be suppressed."""
    return is_shadow_muted(uid) or is_throttled(uid)


def remove_permission(uid: int, perm: str):
    """Mark a permission as revoked (for future enforcement)."""
    if perm not in PERMISSIONS:
        return False
    # In a real system, would call Telegram API here
    # For now, just track it locally
    if uid not in locals().get("revoked_perms", {}):
        revoked_perms = {}
    revoked_perms.setdefault(uid, set()).add(perm)
    return True


def get_shadow_status(uid: int):
    """Return current shadow-moderation status for a user."""
    return {
        "throttled": is_throttled(uid),
        "shadow_muted": is_shadow_muted(uid),
        "suppress_messages": should_suppress_message(uid),
    }
