"""Simple load test generator for the anti-fraud system.

The script repeatedly POSTs fake messages/joins to the webhook endpoint. It can be used
to measure throughput and observe how the worker/queue scales.

Usage:
    python tools/load_test.py --url http://localhost:8000/webhook --rate 500 --duration 60

This will send ~500 events per second for one minute.
"""
import argparse
import asyncio
import json
import random
import time

import aiohttp


def make_event(event_type: str, chat_id: int = 12345):
    base = {
        "chat": chat_id,
        "ts": time.time(),
    }
    if event_type == "message":
        base.update({
            "type": "message",
            "uid": random.randint(1000, 9999),
            "signal_type": random.choice(["velocity", "honeypot"]),
            "value": random.random() * 100,
        })
    else:
        base.update({
            "type": "join",
            "uid": random.randint(1000, 9999),
        })
    return base

async def send_events(url: str, rate: int, duration: int):
    interval = 1.0 / rate
    end = time.time() + duration
    async with aiohttp.ClientSession() as session:
        while time.time() < end:
            evt = make_event(random.choice(["message", "join"]))
            try:
                await session.post(url, json=evt)
            except Exception:
                pass
            await asyncio.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Load test the webhook")
    parser.add_argument("--url", required=True)
    parser.add_argument("--rate", type=int, default=100)
    parser.add_argument("--duration", type=int, default=30)
    args = parser.parse_args()
    asyncio.run(send_events(args.url, args.rate, args.duration))


if __name__ == "__main__":
    main()
