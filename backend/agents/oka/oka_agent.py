# backend/agents/oka/oka_agent.py

from backend.agents.oka.broker_agent import BrokerAgent
from backend.agents.oka.matching_agent import MatchingAgent
from backend.agents.oka.action_agent import ActionAgent

class OKAAgent:
    def __init__(self):
        self.broker_agent = BrokerAgent()
        self.matching_agent = MatchingAgent()
        self.action_agent = ActionAgent()

    def handle(self, user_message: str, user_id: str) -> str:
        # Step 1: Broker agent captures needs
        needs = self.broker_agent.gather_needs(user_message, user_id)

        # Step 2: Matching agent ranks best fits
        matches = self.matching_agent.rank_listings(needs)

        # Step 3: If high-quality match, handoff to associate
        if self.action_agent.should_handoff(matches):
            self.action_agent.send_to_crm(user_id, matches)
            return "✅ I've found some great matches! A human agent will reach out shortly."

        # Otherwise, continue the conversation
        return f"Here are some options: {matches}"
