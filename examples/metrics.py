# métricas de ejemplo

def compute_metrics(events):
    total = len(events)
    blocked = sum(1 for e in events if e.get("action") in ("kick","restrict"))
    return {
        "total_events": total,
        "blocked_actions": blocked,
        "rate": blocked / total if total else 0
    }
