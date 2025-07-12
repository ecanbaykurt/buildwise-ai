# backend/agents/ada/ada_agent.py

from backend.agents.ada.lease_agent import LeaseAgent
from backend.agents.ada.decision_agent import DecisionAgent
from backend.agents.ada.crm_agent import CRMUpdateAgent

class ADAAgent:
    def __init__(self):
        self.lease_agent = LeaseAgent()
        self.decision_agent = DecisionAgent()
        self.crm_agent = CRMUpdateAgent()

    def handle(self, user_message: str, user_id: str) -> str:
        # Example: run lease estimates
        lease_details = self.lease_agent.get_lease_terms(user_message)

        # Example: get negotiation help
        decision_tips = self.decision_agent.get_decision_support(lease_details)

        # Example: update CRM with conversation summary
        self.crm_agent.update(user_id, lease_details, decision_tips)

        return f"Here’s what I found:\nLease: {lease_details}\nTips: {decision_tips}"
