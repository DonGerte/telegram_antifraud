"""Lightweight Python client (SDK) for the Anti-Fraud Moderator Dashboard API.

This is intended for integration into other Python projects or automation scripts.
Example:

    from tools.sdk import AntiFraudClient

    client = AntiFraudClient(base_url="http://localhost:8000")
    stats = client.get_stats()
    users = client.list_users(min_score=30)
"""

import requests


class AntiFraudClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base = base_url.rstrip("/")
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _url(self, path: str) -> str:
        return f"{self.base}{path}"

    def get_stats(self) -> dict:
        resp = self.session.get(self._url("/api/stats"))
        resp.raise_for_status()
        return resp.json()

    def list_users(self, **filters) -> list:
        resp = self.session.get(self._url("/api/users"), params=filters)
        resp.raise_for_status()
        return resp.json()

    def get_user(self, uid: int) -> dict:
        resp = self.session.get(self._url(f"/api/users/{uid}"))
        resp.raise_for_status()
        return resp.json()

    def take_action(self, uid: int, action: str, chat_id: int, reason: str, moderator: str) -> dict:
        data = {
            "action": action,
            "chat_id": chat_id,
            "reason": reason,
            "moderator": moderator,
        }
        resp = self.session.post(self._url(f"/api/users/{uid}/action"), json=data)
        resp.raise_for_status()
        return resp.json()

    def list_rules(self) -> list:
        resp = self.session.get(self._url("/api/rules"))
        resp.raise_for_status()
        return resp.json()

    def create_rule(self, rule: dict) -> dict:
        resp = self.session.post(self._url("/api/rules"), json=rule)
        resp.raise_for_status()
        return resp.json()

    def audit_log(self, hours: int = 24, limit: int = 100) -> list:
        params = {"hours": hours, "limit": limit}
        resp = self.session.get(self._url("/api/audit"), params=params)
        resp.raise_for_status()
        return resp.json()


# example usage when executed as script
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Demo client")
    parser.add_argument("--base", default="http://localhost:8000")
    args = parser.parse_args()

    client = AntiFraudClient(args.base)
    print(client.get_stats())
