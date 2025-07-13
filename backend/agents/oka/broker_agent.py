# backend/agents/oka/broker_agent.py

class BrokerAgent:
    def collect_preferences(self, user_message: str, user_id: str) -> dict:
        print(f"[BrokerAgent] Processing: {user_message} for user: {user_id}")
        return {
            "budget": "$3000/month",
            "pets": True,
            "location": "Downtown",
            "must_haves": ["balcony", "parking"]
        }
