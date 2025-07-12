# backend/agents/oka/action_agent.py

class ActionAgent:
    """
    Checks if lead is qualified.
    If yes, pushes chat summary to CRM or notifies a human associate.
    """
    def __init__(self):
        pass

    def should_handoff(self, matches: list) -> bool:
        return len(matches) > 0  # Simple: if we found good matches

    def push_to_crm(self, user_id: str, preferences: dict, matches: list):
        print(f"[ActionAgent] Pushing lead for {user_id} with {matches} to CRM!")
