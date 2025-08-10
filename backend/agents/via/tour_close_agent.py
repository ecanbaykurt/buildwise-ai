from pydantic import BaseModel
from typing import List, Dict, Any

class ActionPlan(BaseModel):
    actions: List[Dict[str, Any]]
    confirmation_prompt: str

class TourCloseAgent:
    def __init__(self, calendar_slots: List[Dict[str, str]]):
        self.slots = calendar_slots

    def run(self, matches: List[Dict[str, Any]], user_profile: Dict[str, Any] | None = None) -> ActionPlan:
        proposals = []
        for m in matches[:2]:
            # pick earliest available slot
            slot = self.slots[0] if self.slots else {"start":"2025-08-12T15:30:00Z","end":"2025-08-12T16:00:00Z"}
            proposals.append({
                "type":"tour",
                "unit_id": m.get("id"),
                "address": m.get("row_preview",{}).get("address",""),
                "start": slot["start"],
                "end": slot["end"],
                "required_docs": ["photo_id","income_proof"]
            })
        confirm = "Would you like me to book the first tour, the second tour, or propose other times?"
        return ActionPlan(actions=proposals, confirmation_prompt=confirm)
