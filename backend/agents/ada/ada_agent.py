# backend/agents/ada/ada_agent.py

from backend.agents.ada.lease_agent import LeaseAgent
from backend.agents.ada.crm_agent import CRMAgent
from backend.agents.ada.decision_agent import DecisionAgent

class ADAAgent:
    def __init__(self):
        self.lease_agent = LeaseAgent()
        self.crm_agent = CRMAgent()
        self.decision_agent = DecisionAgent()

    def handle(self, user_input):
        lease_info = self.lease_agent.explain_terms(user_input)
        decision_info = self.decision_agent.support_negotiation(lease_info)
        crm_update = self.crm_agent.log_agreement(decision_info)

        return f"Lease Details: {lease_info} | Decision: {decision_info} | CRM Update: {crm_update}"
