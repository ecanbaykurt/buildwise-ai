# backend/agents/agent_manager.py

from backend.agents.oka.oka_agent import OKAAgent
from backend.agents.ada.ada_agent import ADAAgent

class AgentManager:
    def __init__(self):
        self.oka_agent = OKAAgent()
        self.ada_agent = ADAAgent()

    def handle_request(self, user_input):
        oka_result = self.oka_agent.handle(user_input)
        if "handoff to ada" in oka_result.lower():
            ada_result = self.ada_agent.handle(user_input)
            return f"OKA: {oka_result}\nADA: {ada_result}"
        return oka_result
