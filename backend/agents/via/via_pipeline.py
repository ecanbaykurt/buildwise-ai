from .needs_agent.py import NeedsAgent
from .match_rank_agent import MatchRankAgent
from .tour_close_agent import TourCloseAgent
from typing import Dict, Any, List

class VIAAgent:
    def __init__(self, inventory_rows: List[Dict[str, Any]], calendar_slots: List[Dict[str,str]]):
        self.inventory = inventory_rows
        self.calendar = calendar_slots
        self.needs = NeedsAgent()
        self.closer = TourCloseAgent(calendar_slots)

    def handle(self, user_text: str, sample_rows: str | None = None) -> Dict[str, Any]:
        spec = self.needs.run(user_text=user_text, sample_rows=sample_rows)
        matcher = MatchRankAgent(inventory_rows=self.inventory)
        mres = matcher.run(spec=spec.model_dump())
        plan = self.closer.run([m.model_dump() for m in mres.matches])
        return {
            "stage":"VIA",
            "search_spec": spec.model_dump(),
            "matches": [m.model_dump() for m in mres.matches],
            "action_plan": plan.model_dump()
        }
