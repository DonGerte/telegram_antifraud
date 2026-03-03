"""Structured JSON logging for observability and audit trails."""
import json
import logging
import sys
from datetime import datetime

# Logging level constants
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR

class JSONFormatter(logging.Formatter):
    """Formatter that outputs structured JSON logs."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "chat_id"):
            log_data["chat_id"] = record.chat_id
        if hasattr(record, "action"):
            log_data["action"] = record.action
        if hasattr(record, "reason"):
            log_data["reason"] = record.reason
        if hasattr(record, "score"):
            log_data["score"] = record.score
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        return json.dumps(log_data, ensure_ascii=False)


def get_logger(name, level=INFO):
    """Get a JSON-structured logger for the given module name."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add JSON handler to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def log_event(logger, event_type, **kwargs):
    """Log a structured event with type and custom fields."""
    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=f"event: {event_type}",
        args=(),
        exc_info=None
    )
    record.event_type = event_type
    for key, value in kwargs.items():
        setattr(record, key, value)
    logger.handle(record)


def log_action(logger, action, user_id=None, chat_id=None, reason=None, **context):
    """Log an action taken by the system."""
    log_event(logger, "action", action=action, user_id=user_id,
              chat_id=chat_id, reason=reason, context=context)


def log_score_update(logger, user_id, score, chat_id=None, signal_type=None):
    """Log a user score update."""
    log_event(logger, "score_update", user_id=user_id, score=score,
              chat_id=chat_id, signal_type=signal_type)
