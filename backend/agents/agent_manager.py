# backend/agents/agent_manager.py

from backend.agents.oka.oka_agent import OKAAgent
from backend.agents.ada.ada_agent import ADAAgent

class AgentManager:
    def __init__(self):
        self.oka_agent = OKAAgent()
        self.ada_agent = ADAAgent()

    def route_message(self, user_message: str, user_id: str, has_lease: bool) -> str:
        """
        Main entry point: decides whether to run OKA or ADA.
        """
        if has_lease:
            # This user already has a lease → ADA handles lease, CRM, decision help.
            return self.ada_agent.handle(user_message, user_id)
        else:
            # New prospect → OKA handles property info, match, env risk, handoff.
            return self.oka_agent.handle(user_message, user_id)
