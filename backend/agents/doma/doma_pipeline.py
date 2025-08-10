from .lease_qa_agent import LeaseQAAgent
from .service_triage_agent import ServiceTriageAgent
from .renewal_deal_agent import RenewalDealAgent
from typing import Dict, Any, List

class DOMAAgent:
    def __init__(self):
        self.lease = LeaseQAAgent()
        self.triage = ServiceTriageAgent()
        self.renewal = RenewalDealAgent()

    def handle_lease(self, question: str, retrieved_chunks: List[Dict[str, Any]]):
        ans = self.lease.run(question, retrieved_chunks)
        return {"stage":"DOMA","lease_answer": ans.model_dump()}

    def handle_triage(self, ticket_text: str, photos: List[str] | None = None):
        res = self.triage.run(ticket_text, photos)
        return {"stage":"DOMA","triage": res.model_dump()}

    def handle_renewal(self, current_rent: float, comps_median: float, policy_floor: float, policy_ceiling: float):
        pkg = self.renewal.run(current_rent, comps_median, policy_floor, policy_ceiling)
        return {"stage":"DOMA","renewal": pkg.model_dump()}
