# backend/agents/ada/decision_agent.py

class DecisionAgent:
    """
    Helps with simple negotiation or renewal logic.
    """
    def __init__(self):
        pass

    def suggest_adjustments(self, lease_info: str) -> str:
        print(f"[DecisionAgent] Reviewing: {lease_info}")
        return "We can offer a 5% discount if you renew before next month."
