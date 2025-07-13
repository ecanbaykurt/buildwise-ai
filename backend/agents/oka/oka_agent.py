from backend.agents.oka.broker_agent import BrokerAgent
from backend.agents.oka.matching_agent import MatchingAgent
from backend.agents.oka.action_agent import ActionAgent

class OKAAgent:
    def __init__(self):
        self.broker_agent = BrokerAgent()
        self.matching_agent = MatchingAgent()
        self.action_agent = ActionAgent()

    def handle(self, user_message: str) -> str:
        reply1 = self.broker_agent.handle(user_message)
        reply2 = self.matching_agent.rank_properties(user_message)
        reply3 = self.action_agent.create_followup(user_message)
        return f"{reply1}\n\n{reply2}\n\n{reply3}"
