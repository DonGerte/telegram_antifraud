import json


class RuleEngine:
    """Configuration-based rule engine for deciding which actions to take.

    Format is a list of rule entries:
        {
            "name": "rule_name",
            "enabled": true,
            "condition": {
                "score_gt": 50,
                "cluster_gt": 2,
                "has_signal": ["link", "honeypot"],
                "velocity_gt": 30,
                "cluster_and_score": true
            },
            "action": "kick",
            "reason": "multiple suspicious factors",
            "priority": 1
        }

    Conditions available:
      - score_gt, score_lt, score_eq: numeric comparisons on user score
      - cluster_gt, cluster_lt: group size conditions
      - has_signal: single or list of signal types (requires at least one)
      - velocity_gt, velocity_lt: message rate conditions
      - repetition_gt: repeat message count
      - cluster_and_score: AND logic if multiple conditions (default OR)
      - raid_active: true if raid detected in chat

    Actions:
      - kick: remove user from chat
      - mute: silence user messages
      - restrict: limit interaction
      - raid_alert: trigger containment mode
      - none: log only
    """

    def __init__(self, rules=None):
        self.rules = rules or []

    @classmethod
    def load_file(cls, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(data)

    def save_file(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.rules, f, indent=2, ensure_ascii=False)

    def evaluate(self, context):
        """Return list of actions to take given context.
        
        Context fields:
            - score (float): user's current score
            - cluster_size (int): size of user's cluster
            - signals (list): signal types for this event
            - velocity (int): messages/hour
            - repetition (int): count of repeated message
            - raid_detected (bool): is raid active in chat
        """
        results = []
        for rule in self.rules:
            if not rule.get("enabled", True):
                continue
            if self._match(rule.get("condition", {}), context):
                action_name = rule.get("action", "none")
                action = {
                    "action": action_name,
                    "rule": rule.get("name"),
                    "priority": rule.get("priority", 0)
                }
                if "reason" in rule:
                    action["reason"] = rule["reason"]
                results.append(action)
        # Sort by priority (higher first)
        results.sort(key=lambda x: x.get("priority", 0), reverse=True)
        return results

    def _match(self, cond, ctx):
        """Check if all conditions in 'cond' match context 'ctx'."""
        if not cond:
            return True
        
        # Determine if we use AND (all must match) or OR (any must match)
        use_and = cond.get("cluster_and_score", False)
        
        checks = []
        
        # Score checks
        if "score_gt" in cond:
            score = ctx.get("score", 0)
            checks.append(score > cond["score_gt"])
        if "score_lt" in cond:
            score = ctx.get("score", 0)
            checks.append(score < cond["score_lt"])
        if "score_eq" in cond:
            score = ctx.get("score", 0)
            checks.append(score == cond["score_eq"])
        
        # Cluster checks
        if "cluster_gt" in cond:
            cluster = ctx.get("cluster_size", 1)
            checks.append(cluster > cond["cluster_gt"])
        if "cluster_lt" in cond:
            cluster = ctx.get("cluster_size", 1)
            checks.append(cluster < cond["cluster_lt"])
        
        # Signal checks
        if "has_signal" in cond:
            has_sig = cond["has_signal"]
            if isinstance(has_sig, str):
                has_sig = [has_sig]
            signals = set(ctx.get("signals", []))
            checks.append(any(s in signals for s in has_sig))
        
        # Velocity checks
        if "velocity_gt" in cond:
            velocity = ctx.get("velocity", 0)
            checks.append(velocity > cond["velocity_gt"])
        if "velocity_lt" in cond:
            velocity = ctx.get("velocity", 0)
            checks.append(velocity < cond["velocity_lt"])
        
        # Repetition checks
        if "repetition_gt" in cond:
            rep = ctx.get("repetition", 0)
            checks.append(rep > cond["repetition_gt"])
        
        # Raid checks
        if "raid_active" in cond:
            raid = ctx.get("raid_detected", False)
            checks.append(raid == cond["raid_active"])
        
        if not checks:
            return True
        
        if use_and:
            return all(checks)
        else:
            return any(checks)
