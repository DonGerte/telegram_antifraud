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
import config

# Redis queue names
IN_QUEUE = "data_bus"
OUT_QUEUE = "action_bus"

logging.basicConfig(level=logging.INFO)

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
    logging.info(f"enqueue {event}")
    if not redis_client:
        logging.warning("redis not configured, cannot enqueue")
        return
    try:
        redis_client.rpush(OUT_QUEUE, json.dumps(event))
    except Exception as e:
        logging.error(f"failed to enqueue action: {e}")


@bot.on_message(filters.group)
def ingest(client, message):
    uid = message.from_user.id if message.from_user else None
    if not uid:
        return
    sig_type, sig_value = compute_signal(message)
    event = {
        "type": "message",
        "uid": uid,
        "chat": message.chat.id,
        "ts": message.date.timestamp(),
        "signal_type": sig_type,
        "value": sig_value,
        "raw": message.text or message.caption or ""
    }
    try:
        redis_client.rpush(IN_QUEUE, json.dumps(event))
    except Exception as e:
        logging.error(f"failed to send event: {e}")


@bot.on_chat_member()
def member_change(client, event):
    # track joins and leaves for raid detection
    if event.new_chat_member and event.new_chat_member.status == "member":
        uid = event.new_chat_member.user.id
        chat_id = event.chat.id
        ts = event.date.timestamp() if hasattr(event, "date") else time.time()
        join_event = {"type": "join", "chat": chat_id, "uid": uid, "ts": ts}
        try:
            redis_client.rpush(IN_QUEUE, json.dumps(join_event))
        except Exception as e:
            logging.error(f"failed to enqueue join: {e}")


if __name__ == "__main__":
    bot.run()
