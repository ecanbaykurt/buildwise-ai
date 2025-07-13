from backend.agents.ada.lease_agent import LeaseAgent
from backend.agents.ada.decision_agent import DecisionAgent
from backend.agents.ada.crm_agent import CRM_Agent

class ADAAgent:
    def __init__(self):
        self.lease_agent = LeaseAgent()
        self.decision_agent = DecisionAgent()
        self.crm_agent = CRM_Agent()

    def handle(self, user_message: str) -> str:
        reply1 = self.lease_agent.explain_terms(user_message)
        reply2 = self.decision_agent.support_negotiation(user_message)
        reply3 = self.crm_agent.log_agreement(user_message)
        return f"{reply1}\n\n{reply2}\n\n{reply3}"
