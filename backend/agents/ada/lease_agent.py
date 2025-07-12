# backend/agents/ada/lease_agent.py

class LeaseAgent:
    """
    Answers lease term questions, payment details, rules.
    """
    def __init__(self):
        pass

    def explain_lease(self, user_message: str) -> str:
        print(f"[LeaseAgent] Explaining lease: {user_message}")
        return "Your lease is 12 months with a $500 deposit."
