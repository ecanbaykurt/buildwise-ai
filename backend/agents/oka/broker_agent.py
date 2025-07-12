# backend/agents/oka/broker_agent.py

class BrokerAgent:
    """
    Engages the new prospect.
    Gathers info: budget, pets, location, must-haves.
    """
    def __init__(self):
        pass

    def collect_preferences(self, user_message: str) -> dict:
        # Placeholder logic
        print(f"[BrokerAgent] Processing: {user_message}")
        return {
            "budget": "$3000/month",
            "pets": True,
            "location": "Downtown",
            "must_haves": ["balcony", "parking"]
        }
