from backend.agents.oka.oka_agent import OKAAgent as AYAAgent
from backend.agents.ada.ada_agent import ADAAgent as KAYAAgent

class AgentManager:
    def __init__(self):
        self.aya_agent = AYAAgent()
        self.kaya_agent = KAYAAgent()

    def handle(self, user_message: str) -> str:
        """
        Switch logic for which macro agent to call.
        If the message mentions 'lease' or 'renewal', send to KAYAAgent.
        Otherwise, handle with AYAAgent.
        """
        if "lease" in user_message.lower() or "renewal" in user_message.lower():
            return self.kaya_agent.handle(user_message)
        else:
            return self.aya_agent.handle(user_message)
