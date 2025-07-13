from backend.agents.oka.oka_agent import OKAAgent
from backend.agents.ada.ada_agent import ADAAgent

class AgentManager:
    def __init__(self):
        self.oka_agent = OKAAgent()
        self.ada_agent = ADAAgent()

    def handle(self, user_message: str) -> str:
        if "lease" in user_message.lower() or "renewal" in user_message.lower():
            return self.ada_agent.handle(user_message)
        else:
            return self.oka_agent.handle(user_message)
