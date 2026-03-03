from pyrogram import Client
import logging
import time
import json

try:
    import redis
except ImportError:
    redis = None

import config
from engine import raid, shadow_mod
from engine.logger import get_logger, log_event

log = get_logger("private_bot")

_redis = None
if redis and config.REDIS_URL:
    try:
        _redis = redis.from_url(config.REDIS_URL)
    except Exception:
        _redis = None

priv_bot = Client("private_bot", bot_token=config.PRIVATE_BOT_TOKEN)

ACTION_QUEUE = "action_bus"



def kick_user(chat_id: int, user_id: int, reason=None):
    """Kick a user from a chat."""
    try:
        priv_bot.kick_chat_member(chat_id, user_id)
        log_event(log, "user_kicked", chat_id=chat_id, user_id=user_id, reason=reason)
    except Exception as e:
        log.error(f"kick failed {user_id}@{chat_id}: {e}")


def mute_user(chat_id: int, user_id: int, duration: int = 3600):
    """Mute a user for duration seconds."""
    try:
        shadow_mod.shadow_mute(user_id, duration)
        log_event(log, "user_muted", chat_id=chat_id, user_id=user_id, duration=duration)
    except Exception as e:
        log.error(f"mute failed {user_id}@{chat_id}: {e}")


def restrict_user(chat_id: int, user_id: int, reason=None):
    """Restrict a user's permissions."""
    try:
        shadow_mod.throttle_user(user_id, msgs_per_minute=1)
        log_event(log, "user_restricted", chat_id=chat_id, user_id=user_id, reason=reason)
    except Exception as e:
        log.error(f"restrict failed {user_id}@{chat_id}: {e}")


def enable_slow_mode(chat_id: int):
    """Enable slow mode in a chat."""
    try:
        raid.enter_containment(chat_id, "slow")
        log_event(log, "slow_mode_enabled", chat_id=chat_id)
    except Exception as e:
        log.error(f"slow mode failed {chat_id}: {e}")


def enable_bunker_mode(chat_id: int):
    """Enable bunker (lockdown) mode in a chat."""
    try:
        raid.enter_containment(chat_id, "bunker")
        log_event(log, "bunker_mode_enabled", chat_id=chat_id)
    except Exception as e:
        log.error(f"bunker mode failed {chat_id}: {e}")


def disable_containment(chat_id: int):
    """Disable containment mode in a chat."""
    try:
        raid.exit_containment(chat_id)
        log_event(log, "containment_disabled", chat_id=chat_id)
    except Exception as e:
        log.error(f"disable containment failed {chat_id}: {e}")


def process_action(raw):
    """Process an action from the action_bus queue."""
    try:
        action = json.loads(raw)
    except Exception as e:
        log.error(f"malformed action: {raw}, error: {e}")
        return
    
    act = action.get("action")
    
    if act == "kick":
        kick_user(action.get("chat"), action.get("uid"), action.get("reason"))
    elif act == "mute":
        mute_user(action.get("chat"), action.get("uid"), action.get("duration", 3600))
    elif act == "restrict":
        restrict_user(action.get("chat"), action.get("uid"), action.get("reason"))
    elif act == "raid_alert":
        enable_slow_mode(action.get("chat"))
    elif act == "raid_bunker":
        enable_bunker_mode(action.get("chat"))
    elif act == "containment_off":
        disable_containment(action.get("chat"))
    else:
        log.info(f"unhandled action {act}")


def main():
    if not _redis:
        log.error("redis not configured, cannot consume actions")
        return
    log.info("private bot listening for actions")
    while True:
        try:
            _, raw = _redis.blpop(ACTION_QUEUE, timeout=5)
            if raw:
                process_action(raw)
        except Exception as e:
            log.error(f"error processing action: {e}")
            time.sleep(1)


if __name__ == "__main__":
    # Start listening on a background thread while bot runs
    import threading
    action_thread = threading.Thread(target=main, daemon=True)
    action_thread.start()
    
    try:
        priv_bot.start()
    finally:
        priv_bot.stop()
