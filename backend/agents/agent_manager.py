# backend/agents/agent_manager.py

from backend.agents.oka.oka_agent import OKAAgent
from backend.agents.ada.ada_agent import ADAAgent

class AgentManager:
    def __init__(self):
        self.oka_agent = OKAAgent()
        self.ada_agent = ADAAgent()

    def handle_request(self, user_input):
        """
        1. OKA handles the lead, matching, broker flow
        2. If the result indicates a lease or CRM follow-up, pass to ADA
        """
        oka_response = self.oka_agent.handle(user_input)

        # 💡 Example: Look for keyword trigger — you can improve with your real flow!
        if "handoff to ada" in oka_response.lower():
            ada_response = self.ada_agent.handle(user_input)
            return f"OKA: {oka_response}\n\nADA: {ada_response}"
        else:
            return oka_response
