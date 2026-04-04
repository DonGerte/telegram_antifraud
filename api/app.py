from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from datetime import datetime

import config
from services import db
from engine.risk_assessment import assess_user_risk
from services.user_history import get_user_events

app = FastAPI(title="Telegram Antifraud API", version="0.1.0")


def validate_api_key(x_api_key: str = Header(None)):
    if not config.API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY is not configured")
    if x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return x_api_key


class EventPayload(BaseModel):
    user_id: int
    chat_id: int
    signal: str
    value: float
    raw_text: str = ""
    ts: datetime = None


@app.on_event("startup")
async def startup_event():
    db.init_db()


@app.get("/api/v1/user/{user_id}")
async def user_status(user_id: int, api_key: str = Depends(validate_api_key)):
    events = get_user_events(user_id)
    if not events:
        raise HTTPException(status_code=404, detail="User not found")
    risk = assess_user_risk(user_id, events[0]["chat_id"], events[-1].get("raw_text", ""))
    return {"user_id": user_id, "risk": risk, "events": events[-10:]}


@app.post("/api/v1/event")
async def post_event(evt: EventPayload, api_key: str = Depends(validate_api_key)):
    db.create_event({
        "user_id": evt.user_id,
        "chat_id": evt.chat_id,
        "signal": evt.signal,
        "value": evt.value,
        "ts": evt.ts or datetime.utcnow(),
        "raw_text": evt.raw_text,
    })
    return {"status": "ok", "user_id": evt.user_id}


@app.get("/api/v1/alerts")
async def alerts(api_key: str = Depends(validate_api_key)):
    # simple alert feed (last 20 dangerous users)
    return {"alerts": []}
