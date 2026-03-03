"""PagerDuty integration for critical alerts.

Send incidents to PagerDuty for on-call escalation.
"""

import requests
import json
from typing import Dict, List
import os
from datetime import datetime

class PagerDutyClient:
    """Send alerts to PagerDuty."""
    
    def __init__(self, integration_key: str = None):
        self.integration_key = integration_key or os.getenv("PAGERDUTY_INTEGRATION_KEY")
        self.api_url = "https://events.pagerduty.com/v2/enqueue"
        self.enabled = bool(self.integration_key)
    
    def send_incident(
        self,
        severity: str,
        title: str,
        description: str,
        details: Dict = None,
        dedup_key: str = None
    ) -> Dict:
        """Create a PagerDuty incident.
        
        Args:
            severity: "critical", "error", "warning", "info"
            title: Brief incident title
            description: Detailed description
            details: Additional context dict
            dedup_key: Deduplication key (prevent duplicates)
            
        Returns:
            Response from PagerDuty API
        """
        if not self.enabled:
            return {"status": "disabled"}
        
        payload = {
            "routing_key": self.integration_key,
            "event_action": "trigger",
            "dedup_key": dedup_key or f"{title}_{int(datetime.now().timestamp())}",
            "payload": {
                "summary": title,
                "severity": severity,
                "source": "Telegram Antifraud",
                "component": "worker",
                "custom_details": {
                    "description": description,
                    **(details or {})
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"PagerDuty API error: {e}")
            return {"status": "error", "message": str(e)}
    
    def resolve_incident(self, dedup_key: str) -> Dict:
        """Resolve an incident."""
        if not self.enabled:
            return {"status": "disabled"}
        
        payload = {
            "routing_key": self.integration_key,
            "event_action": "resolve",
            "dedup_key": dedup_key
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"PagerDuty API error: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_alert(
        self,
        alert_type: str,
        message: str,
        details: Dict = None
    ) -> Dict:
        """Send an alert with appropriate severity mapping."""
        severity_map = {
            "database_down": "critical",
            "worker_error": "error",
            "high_latency": "warning",
            "raid_detected": "warning",
            "rule_error": "error"
        }
        
        severity = severity_map.get(alert_type, "warning")
        return self.send_incident(
            severity=severity,
            title=f"[{alert_type.upper()}] {message[:80]}",
            description=message,
            details=details,
            dedup_key=f"antifraud_{alert_type}"
        )


# Integration with existing alerting
class AlertManager:
    """Unified alert manager supporting multiple channels."""
    
    def __init__(self):
        self.pagerduty = PagerDutyClient()
        self.channels = {
            "pagerduty": self.pagerduty.send_alert,
            "slack": self._send_slack,
            "email": self._send_email,
        }
    
    def _send_slack(self, alert_type: str, message: str, details: Dict = None) -> Dict:
        """Send to Slack (requires webhook URL)."""
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            return {"status": "disabled"}
        
        payload = {
            "text": f"🚨 {alert_type}: {message}",
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*{alert_type.upper()}*\n{message}"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": f"```{json.dumps(details, indent=2)}```"}} if details else None
            ]
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=5)
            return {"status": "sent"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _send_email(self, alert_type: str, message: str, details: Dict = None) -> Dict:
        """Send email alert (requires smtp config)."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            smtp_server = os.getenv("SMTP_SERVER")
            from_addr = os.getenv("ALERT_FROM_EMAIL")
            to_addr = os.getenv("ALERT_TO_EMAIL")
            
            if not all([smtp_server, from_addr, to_addr]):
                return {"status": "disabled"}
            
            msg = MIMEText(f"{alert_type.upper()}\n\n{message}\n\nDetails:\n{json.dumps(details, indent=2)}")
            msg["Subject"] = f"[Antifraud] {alert_type}: {message[:50]}"
            msg["From"] = from_addr
            msg["To"] = to_addr
            
            with smtplib.SMTP(smtp_server, 587) as server:
                server.starttls()
                server.login(from_addr, os.getenv("SMTP_PASSWORD"))
                server.send_message(msg)
            
            return {"status": "sent"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def alert(
        self,
        alert_type: str,
        message: str,
        channels: List[str] = None,
        details: Dict = None
    ) -> Dict:
        """Send alert to specified channels (default: all enabled)."""
        if channels is None:
            channels = list(self.channels.keys())
        
        results = {}
        for channel in channels:
            if channel in self.channels:
                results[channel] = self.channels[channel](alert_type, message, details)
        
        return results


# Example usage
if __name__ == "__main__":
    manager = AlertManager()
    
    # Send critical alert
    result = manager.alert(
        alert_type="database_down",
        message="PostgreSQL connection lost - 5min downtime",
        channels=["pagerduty", "slack", "email"],
        details={
            "component": "postgres",
            "last_connection": "2026-03-03T14:23:45Z",
            "error": "connection timeout",
            "action": "escalating to DBA"
        }
    )
    
    print("Alert results:", result)
    
    # Resolve incident
    pagerduty = PagerDutyClient()
    resolve_result = pagerduty.resolve_incident("antifraud_database_down")
    print("Resolution result:", resolve_result)
