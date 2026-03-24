from pyrogram import Client, filters
import logging
import os
import json
import time
import hashlib
from collections import defaultdict

try:
    import redis
except ImportError:
    redis = None

from engine import honeypot
from engine.heuristics import compute_signal
from engine.risk_assessment import assess_user_risk, should_action_on_message
from services import memory, strike_manager, ban_manager
import config

# Redis queue names
IN_QUEUE = "data_bus"
OUT_QUEUE = "action_bus"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("public_bot")

# connect to Redis broker
redis_client = None
if redis:
    try:
        redis_client = redis.from_url(config.REDIS_URL)
    except Exception:
        redis_client = None

bot = Client("public_bot", bot_token=config.PUBLIC_BOT_TOKEN)

def enqueue_action(action, payload):
    event = {"action": action, **payload}
    logger.info(f"enqueue {event}")
    if not redis_client:
        logger.warning("redis not configured, cannot enqueue")
        return
    try:
        redis_client.rpush(OUT_QUEUE, json.dumps(event))
    except Exception as e:
        logger.error(f"failed to enqueue action: {e}")


@bot.on_message(filters.group)
def ingest(client, message):
    uid = message.from_user.id if message.from_user else None
    if not uid:
        return
    
    # Record message in memory
    text = message.text or message.caption or ""
    memory.record_message(uid, text, message.chat.id)
    
    # Get signal from heuristics
    sig_type, sig_value = compute_signal(message)
    
    # Assess overall risk
    risk_result = assess_user_risk(uid, message.chat.id, text)
    
    logger.info(
        f"[{message.chat.id}] User {uid} | Signal: {sig_type} ({sig_value}) | "
        f"Risk: {risk_result['level']} ({risk_result['score']:.0f})"
    )
    
    # Determine if action needed
    should_act, action = should_action_on_message(risk_result)
    
    if should_act:
        if action == "STRIKE":
            strikes = strike_manager.process_strike(uid, reason=sig_type)
            logger.warning(f"User {uid}: {strikes}")
        elif action == "DELETE":
            logger.error(f"User {uid} banned - deleting message")
    
    # Also send to queue for worker processing (existing system)
    event = {
        "type": "message",
        "uid": uid,
        "chat": message.chat.id,
        "ts": message.date.timestamp(),
        "signal_type": sig_type,
        "value": sig_value,
        "raw": text,
        "risk_level": risk_result["level"],
        "risk_score": risk_result["score"]
    }
    
    try:
        if redis_client:
            redis_client.rpush(IN_QUEUE, json.dumps(event))
    except Exception as e:
        logger.error(f"failed to send event to queue: {e}")


@bot.on_chat_member()
def member_change(client, event):
    # track joins and leaves for raid detection
    if event.new_chat_member and event.new_chat_member.status == "member":
        uid = event.new_chat_member.user.id
        chat_id = event.chat.id
        ts = event.date.timestamp() if hasattr(event, "date") else time.time()
        
        # Check if user is banned
        if ban_manager.is_user_banned(uid):
            logger.warning(f"Banned user {uid} joined {chat_id} - should restrict")
        
        join_event = {"type": "join", "chat": chat_id, "uid": uid, "ts": ts}
        try:
            if redis_client:
                redis_client.rpush(IN_QUEUE, json.dumps(join_event))
        except Exception as e:
            logger.error(f"failed to enqueue join: {e}")


if __name__ == "__main__":
    bot.run()
