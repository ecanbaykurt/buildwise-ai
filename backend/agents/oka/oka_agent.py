# backend/agents/oka_agent.py

"""
OKAAgent: Orchestrates the leasing pipeline by chaining:
1. BrokerAgent: Extracts key user needs.
2. MatchingAgent: Finds matching units.
3. ActionAgent: Suggests clear next steps.
"""

class BrokerAgent:
    """
    BrokerAgent: Extracts core user needs and clarifies vague requests.
    """
    def run(self, user_input: str) -> str:
        prompt = (
            "You are a smart real estate broker. Identify the key user needs in plain language.\n"
            "Summarize location, budget, size, and any special requirements.\n"
            f"User says: '{user_input}'"
        )
        # If connected, here you'd call OpenAI with this prompt.
        # Example placeholder:
        extracted_info = (
            "Extracted: 2-bedroom apartment, max $3000, near Cambridge, quiet neighborhood."
        )
        return extracted_info


class MatchingAgent:
    """
    MatchingAgent: Matches extracted preferences to best-fit units.
    """
    def run(self, broker_summary: str) -> str:
        prompt = (
            "You are a property matching assistant. Based on the broker summary, "
            "select top 3 matching units with rent and location.\n\n"
            f"Broker Summary: '{broker_summary}'"
        )
        # Example placeholder:
        matches = (
            "1. Unit A — 2BR in Porter Square, $2800/mo.\n"
            "2. Unit B — 2BR in Kendall Square, $2900/mo.\n"
            "3. Unit C — 2BR in Inman Square, $2750/mo."
        )
        return matches


class ActionAgent:
    """
    ActionAgent: Generates clear next steps for the user.
    """
    def run(self, matching_results: str) -> str:
        prompt = (
            "As an action agent, suggest practical next steps: "
            "Offer to schedule tours, clarify questions, or finalize lease.\n\n"
            f"Matching Results: '{matching_results}'"
        )
        # Example placeholder:
        next_steps = (
            "Next Steps:\n"
            "- Would you like to tour one of these units?\n"
            "- Any questions about lease length or fees?\n"
            "- Ready to sign? I can pass you to ADAAgent to handle the paperwork."
        )
        return next_steps


class OKAAgent:
    """
    OKAAgent: Coordinates Broker → Matching → Action steps.
    """
    def __init__(self):
        self.broker_agent = BrokerAgent()
        self.matching_agent = MatchingAgent()
        self.action_agent = ActionAgent()

    def handle(self, user_input: str) -> str:
        broker_output = self.broker_agent.run(user_input)
        matching_output = self.matching_agent.run(broker_output)
        action_output = self.action_agent.run(matching_output)

        return (
            f"📌 OKA Agent Workflow:\n\n"
            f"🔍 BrokerAgent: {broker_output}\n\n"
            f"🏠 MatchingAgent: {matching_output}\n\n"
            f"✅ ActionAgent: {action_output}"
        )
