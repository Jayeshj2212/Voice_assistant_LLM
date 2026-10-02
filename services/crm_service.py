import os
from typing import Any, Dict

import requests


class CRMService:
    def __init__(self, api_url: str = "", api_key: str = ""):
        self.api_url = api_url or os.getenv("CRM_API_URL", "")
        self.api_key = api_key or os.getenv("CRM_API_KEY", "")

    def sync_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_url:
            return {"status": "mock-sync", "lead": lead, "message": "CRM not configured; using local mock mode."}

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        response = requests.post(self.api_url, json=lead, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def update_disposition(self, lead_id: str, disposition: str, follow_up: str) -> Dict[str, Any]:
        payload = {"lead_id": lead_id, "disposition": disposition, "follow_up": follow_up}
        if not self.api_url:
            return {"status": "mock-disposition", "payload": payload}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        response = requests.post(f"{self.api_url}/disposition", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
