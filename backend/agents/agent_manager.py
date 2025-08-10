# backend/agents/agent_manager.py

"""
AgentManager:
- Orchestrates the flow between OKAAgent and ADAAgent.
- Always runs OKAAgent first.
- If handoff keyword detected, runs ADAAgent too.
- Combines responses for a complete user answer.
"""

# Use absolute imports (safe for Streamlit Cloud!)
from backend.agents.oka_agent import OKAAgent
from backend.agents.ada_agent import ADAAgent

class AgentManager:
    def __init__(self):
        self.oka_agent = OKAAgent()
        self.ada_agent = ADAAgent()

    def handle_request(self, user_input: str) -> str:
        """
        Runs the OKA workflow first.
        If handoff keyword is found, runs ADA workflow too.
        """
        oka_result = self.oka_agent.handle(user_input)

        # Clear and flexible handoff keywords
        handoff_keywords = ["handoff to ada", "ready to finalize", "finalize lease"]
        if any(keyword in oka_result.lower() for keyword in handoff_keywords):
            ada_result = self.ada_agent.handle(user_input)
            return f"AgentManager Workflow:\n\nOKA: {oka_result}\n\nADA: {ada_result}"

        return f"AgentManager Workflow:\n\nOKA: {oka_result}"
