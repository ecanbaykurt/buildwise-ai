# backend/agents/oka/matching_agent.py

class MatchingAgent:
    """
    Takes user preferences, queries Pinecone or your DB,
    and returns ranked property matches.
    """
    def __init__(self):
        pass

    def rank_properties(self, preferences: dict) -> list:
        # Stub logic
        print(f"[MatchingAgent] Ranking with: {preferences}")
        matches = [
            {"property_id": 101, "score": 0.95},
            {"property_id": 205, "score": 0.90}
        ]
        return matches
