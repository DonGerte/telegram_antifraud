import json
import logging
import os
import time

from fastapi import FastAPI, Header, HTTPException

try:
    import redis
except ImportError:
    redis = None

import config
from engine.heuristics import compute_signal

app = FastAPI()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("webhook")

IN_QUEUE = "data_bus"

redis_client = None
if redis and config.REDIS_URL:
    try:
        redis_client = redis.from_url(config.REDIS_URL)
    except Exception as e:
        log.warning(f"could not connect to Redis: {e}")


def _extract_message(update: dict) -> dict:
    # find standard message payload fields in Telegram update
    for key in ("message", "edited_message", "channel_post", "edited_channel_post"):
        if key in update and isinstance(update[key], dict):
            return update[key]
    return {}


@app.post("/webhook")
async def webhook(update: dict, x_telegram_bot_api_secret_token: str = Header(None)):
    if config.WEBHOOK_SECRET_TOKEN:
        if x_telegram_bot_api_secret_token != config.WEBHOOK_SECRET_TOKEN:
            raise HTTPException(status_code=403, detail="Invalid webhook secret token")

    message = _extract_message(update)
    if not message:
        raise HTTPException(status_code=400, detail="No message payload")

    sender = message.get("from", {})
    uid = sender.get("id")
    chat = message.get("chat", {}).get("id")
    if not uid or not chat:
        raise HTTPException(status_code=400, detail="Missing uid/chat")

    text = message.get("text") or message.get("caption") or ""
    signal_type, signal_value = compute_signal({"from": sender, "text": text, "caption": message.get("caption")})

    event = {
        "type": "message",
        "uid": uid,
        "chat": chat,
        "ts": message.get("date", int(time.time())),
        "signal_type": signal_type,
        "value": signal_value,
        "raw": text,
    }

    if not redis_client:
        log.error("Redis not configured")
        raise HTTPException(status_code=503, detail="Redis not available")

    try:
        redis_client.rpush(IN_QUEUE, json.dumps(event))
    except Exception as e:
        log.error(f"failed enqueue update: {e}")
        raise HTTPException(status_code=500, detail="queue error")

    return {"ok": True}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
