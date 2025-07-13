# backend/agents/oka/oka_agent.py

from backend.agents.oka.broker_agent import BrokerAgent
from backend.agents.oka.matching_agent import MatchingAgent
from backend.agents.oka.action_agent import ActionAgent

class OKAAgent:
    def __init__(self):
        self.broker_agent = BrokerAgent()
        self.matching_agent = MatchingAgent()
        self.action_agent = ActionAgent()

    def handle(self, user_input):
        broker_response = self.broker_agent.run(user_input)
        matching_response = self.matching_agent.run(broker_response)
        action_response = self.action_agent.run(matching_response)

        # Example: Suppose your action_agent decides it needs ADA
        if "finalize lease" in action_response.lower():
            return f"{action_response} | Handoff to ADA"
        return action_response
