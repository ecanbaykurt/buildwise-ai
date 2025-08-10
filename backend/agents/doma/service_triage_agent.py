from pydantic import BaseModel
from typing import Dict, Any, List

class TriageResult(BaseModel):
    category: str
    priority: str
    vendor: str
    eta_hours: int
    confirm_message: str

EMERGENCY_KEYWORDS = {"gas leak","water main break","sparks","smoke"}

class ServiceTriageAgent:
    def run(self, ticket_text: str, photos: List[str] | None = None, roster: Dict[str,str] | None = None) -> TriageResult:
        text_low = ticket_text.lower()
        if any(k in text_low for k in EMERGENCY_KEYWORDS):
            return TriageResult(
                category="emergency",
                priority="P0",
                vendor="dispatch_call_center",
                eta_hours=1,
                confirm_message="Emergency detected. We are dispatching immediately. Please evacuate if unsafe and call local emergency services."
            )
        category = "plumbing" if "leak" in text_low else "hvac" if "ac" in text_low or "air" in text_low else "general"
        vendor = "preferred_plumber_inc" if category == "plumbing" else "preferred_hvac_llc" if category == "hvac" else "handyman_pool"
        eta = 24 if category == "general" else 8
        return TriageResult(
            category=category, priority="P2", vendor=vendor, eta_hours=eta,
            confirm_message=f"Ticket logged as {category}. Assigned {vendor}. Estimated visit within {eta} hours."
        )
