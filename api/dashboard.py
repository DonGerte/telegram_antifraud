"""Moderator dashboard API built with FastAPI.

Endpoints:
  GET  /api/users              - list flagged users with scores
  GET  /api/users/{uid}        - detailed user profile + history
  GET  /api/alerts             - list recent alerts/actions
  GET  /api/stats              - system statistics
  
  POST   /api/users/{uid}/action    - manually kick/mute user
  
  GET    /api/rules            - list all rules
  POST   /api/rules            - create new rule
  PUT    /api/rules/{rid}      - update rule
  DELETE /api/rules/{rid}      - disable rule
  
  GET    /api/audit            - audit trail
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import logging

from db.models import (
    User, Signal, ModAction, Rule, AuditLog, get_db, init_db, SessionLocal
)

app = FastAPI(title="Anti-Fraud Moderator Dashboard", version="1.0")
log = logging.getLogger("dashboard")


# Schemas
class UserProfile(BaseModel):
    telegram_id: int
    username: str | None
    current_score: float
    status: str
    signal_count: int
    action_count: int

class SignalRecord(BaseModel):
    signal_type: str
    value: float
    chat_id: int
    created_at: str

class ActionRecord(BaseModel):
    action: str
    reason: str
    chat_id: int
    created_at: str

class UserDetail(BaseModel):
    profile: UserProfile
    recent_signals: list[SignalRecord]
    recent_actions: list[ActionRecord]

class RuleSchema(BaseModel):
    name: str
    condition: dict
    action: str
    reason: str | None = None
    priority: int = 0
    enabled: bool = True

class ManualActionRequest(BaseModel):
    action: str  # kick, mute, restrict
    chat_id: int
    reason: str
    moderator: str


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/users")
def list_users(
    min_score: float = Query(0, ge=0),
    status: str = Query("all", regex="^(all|normal|restricted|banned)$"),
    limit: int = Query(50, le=1000),
    db: Session = Depends(get_db)
):
    """List flagged users with scores."""
    query = db.query(User).filter(User.current_score >= min_score)
    if status != "all":
        query = query.filter(User.status == status)
    users = query.order_by(User.current_score.desc()).limit(limit).all()
    
    result = []
    for u in users:
        result.append({
            "telegram_id": u.telegram_id,
            "username": u.username,
            "score": u.current_score,
            "status": u.status,
            "signals": len(u.signals),
            "actions": len(u.actions),
            "last_seen": u.last_seen.isoformat() if u.last_seen else None,
        })
    return result


@app.get("/api/users/{uid}")
def get_user(uid: int, db: Session = Depends(get_db)):
    """Get detailed user profile with signal/action history."""
    user = db.query(User).filter(User.telegram_id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    signals = db.query(Signal).filter(Signal.user_id == user.id).order_by(Signal.created_at.desc()).limit(20).all()
    actions = db.query(ModAction).filter(ModAction.user_id == user.id).order_by(ModAction.created_at.desc()).limit(20).all()
    
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "score": user.current_score,
        "status": user.status,
        "created_at": user.created_at.isoformat(),
        "last_seen": user.last_seen.isoformat() if user.last_seen else None,
        "signals": [
            {
                "type": s.signal_type,
                "value": s.value,
                "chat": s.chat_id,
                "created_at": s.created_at.isoformat(),
            }
            for s in signals
        ],
        "actions": [
            {
                "action": a.action,
                "reason": a.reason,
                "chat": a.chat_id,
                "rule": a.rule_name,
                "created_at": a.created_at.isoformat(),
            }
            for a in actions
        ],
    }


@app.get("/api/alerts")
def get_alerts(
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """List recent mod actions (alerts)."""
    since = datetime.utcnow() - timedelta(hours=hours)
    actions = db.query(ModAction).filter(
        ModAction.created_at >= since
    ).order_by(ModAction.created_at.desc()).limit(limit).all()
    
    result = []
    for a in actions:
        user = db.query(User).filter(User.id == a.user_id).first()
        result.append({
            "telegram_id": user.telegram_id if user else None,
            "action": a.action,
            "reason": a.reason,
            "chat": a.chat_id,
            "score": a.score_at_action,
            "rule": a.rule_name,
            "created_at": a.created_at.isoformat(),
        })
    return result


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """System statistics."""
    total_users = db.query(User).count()
    flagged_users = db.query(User).filter(User.current_score > 50).count()
    restricted = db.query(User).filter(User.status == "restricted").count()
    banned = db.query(User).filter(User.status == "banned").count()
    
    today = datetime.utcnow().date()
    today_actions = db.query(ModAction).filter(
        ModAction.created_at >= datetime(today.year, today.month, today.day)
    ).count()
    
    return {
        "total_users": total_users,
        "flagged_users": flagged_users,
        "restricted": restricted,
        "banned": banned,
        "actions_today": today_actions,
    }


@app.post("/api/users/{uid}/action")
def manual_action(
    uid: int,
    req: ManualActionRequest,
    db: Session = Depends(get_db)
):
    """Manually apply an action to a user (for moderators)."""
    user = db.query(User).filter(User.telegram_id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Record the action
    action = ModAction(
        user_id=user.id,
        action=req.action,
        chat_id=req.chat_id,
        reason=req.reason,
        score_at_action=user.current_score,
    )
    db.add(action)
    
    # Update user status if needed
    if req.action == "kick":
        user.status = "banned"
    elif req.action in ("mute", "restrict"):
        user.status = "restricted"
    
    # Log audit
    audit = AuditLog(
        action=f"manual_{req.action}",
        actor=req.moderator,
        target_user_id=user.id,
        details=json.dumps({"reason": req.reason, "chat": req.chat_id}),
    )
    db.add(audit)
    db.commit()
    
    return {"status": "ok", "action": req.action, "user_id": uid}


@app.get("/api/rules")
def list_rules(db: Session = Depends(get_db)):
    """List all rules."""
    rules = db.query(Rule).order_by(Rule.priority.desc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "action": r.action,
            "enabled": r.enabled,
            "priority": r.priority,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
        }
        for r in rules
    ]


@app.post("/api/rules")
def create_rule(rule: RuleSchema, moderator: str = Query(...), db: Session = Depends(get_db)):
    """Create a new rule (stored in DB, can be synced to rules.json)."""
    db_rule = Rule(
        name=rule.name,
        condition=json.dumps(rule.condition),
        action=rule.action,
        reason=rule.reason,
        priority=rule.priority,
        enabled=rule.enabled,
        created_by=moderator,
    )
    db.add(db_rule)
    
    audit = AuditLog(
        action="rule_created",
        actor=moderator,
        target_rule_id=db_rule.id,
        details=json.dumps(rule.dict()),
    )
    db.add(audit)
    db.commit()
    
    return {"id": db_rule.id, "name": rule.name}


@app.put("/api/rules/{rid}")
def update_rule(rid: int, rule: RuleSchema, moderator: str = Query(...), db: Session = Depends(get_db)):
    """Update a rule."""
    db_rule = db.query(Rule).filter(Rule.id == rid).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db_rule.name = rule.name
    db_rule.condition = json.dumps(rule.condition)
    db_rule.action = rule.action
    db_rule.reason = rule.reason
    db_rule.priority = rule.priority
    db_rule.enabled = rule.enabled
    db_rule.version += 1
    db_rule.updated_at = datetime.utcnow()
    
    audit = AuditLog(
        action="rule_updated",
        actor=moderator,
        target_rule_id=rid,
        details=json.dumps(rule.dict()),
    )
    db.add(audit)
    db.commit()
    
    return {"id": rid, "name": rule.name}


@app.delete("/api/rules/{rid}")
def delete_rule(rid: int, moderator: str = Query(...), db: Session = Depends(get_db)):
    """Disable a rule (soft delete)."""
    db_rule = db.query(Rule).filter(Rule.id == rid).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db_rule.enabled = False
    
    audit = AuditLog(
        action="rule_disabled",
        actor=moderator,
        target_rule_id=rid,
    )
    db.add(audit)
    db.commit()
    
    return {"status": "disabled", "rule_id": rid}


@app.get("/api/audit")
def get_audit_log(
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get audit trail."""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "action": l.action,
            "actor": l.actor,
            "target_user": l.target_user_id,
            "target_rule": l.target_rule_id,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
