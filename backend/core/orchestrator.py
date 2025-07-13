from backend.agents.agent_manager import AgentManager

class Orchestrator:
    def __init__(self):
        self.manager = AgentManager()

    def handle_request(self, user_message: str) -> str:
        """
        Entry point for any incoming chat request.
        Calls the Agent Manager, which routes to the right macro agent.
        """
        response = self.manager.handle(user_message)
        return response
