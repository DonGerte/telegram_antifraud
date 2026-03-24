"""Risk assessment engine - wraps scoring with risk levels and recommendations."""
import logging
from typing import Tuple, Dict
from engine import scoring
from engine import raid
from services import memory, ban_manager

logger = logging.getLogger("risk_assessment")


class RiskLevel:
    """Risk classification."""
    SAFE = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    DANGEROUS = "DANGEROUS"
    BANNED = "BANNED"


def assess_user_risk(user_id: int, chat_id: int, text: str = "") -> Dict:
    """
    Comprehensive risk assessment for a user.
    
    Returns:
    {
        "level": RiskLevel (SAFE/SUSPICIOUS/DANGEROUS/BANNED),
        "score": float (0-100),
        "reasons": [list of strings],
        "recommended_action": str,
        "confidence": float (0-1)
    }
    """
    
    # Check if already banned
    if ban_manager.is_user_banned(user_id):
        return {
            "level": RiskLevel.BANNED,
            "score": 100.0,
            "reasons": ["User is banned"],
            "recommended_action": "DELETE",
            "confidence": 1.0
        }
    
    # Get base score from engine
    base_score = scoring.compute_score(user_id)
    
    # Normalize to 0-100
    normalized_score = min(100.0, base_score)
    
    reasons = []
    adjustments = 0
    
    # Check for raid
    if raid.detect_raid(chat_id):
        reasons.append("Chat is under raid")
        adjustments += 15
    
    # Check user memory for patterns
    user_profile = memory.get_user_profile(user_id)
    if user_profile:
        if user_profile["strikes"] > 0:
            reasons.append(f"{user_profile['strikes']}/3 strikes")
            adjustments += user_profile["strikes"] * 10
    
    # Determine level
    adjusted_score = min(100.0, normalized_score + adjustments)
    
    if adjusted_score >= 70:
        level = RiskLevel.DANGEROUS
        action = "BAN"
        confidence = 0.9
    elif adjusted_score >= 40:
        level = RiskLevel.SUSPICIOUS
        action = "WARN"
        confidence = 0.7
    else:
        level = RiskLevel.SAFE
        action = "ALLOW"
        confidence = 0.95
    
    return {
        "level": level,
        "score": adjusted_score,
        "reasons": reasons,
        "recommended_action": action,
        "confidence": confidence,
        "base_score": normalized_score,
        "adjustments": adjustments
    }


def should_action_on_message(risk_result: Dict) -> Tuple[bool, str]:
    """
    Decide if action should be taken based on risk assessment.
    
    Returns: (should_act, action_type)
    """
    level = risk_result["level"]
    
    if level == RiskLevel.DANGEROUS:
        return True, "STRIKE"
    elif level == RiskLevel.SUSPICIOUS:
        return True, "WARN"
    elif level == RiskLevel.BANNED:
        return True, "DELETE"
    
    return False, "NONE"
