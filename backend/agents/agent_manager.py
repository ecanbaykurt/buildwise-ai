# backend/agents/agent_manager.py

"""
AgentManager:
- Orchestrates the flow between OKAAgent and ADAAgent.
- Always runs OKAAgent first.
- If OKAAgent output contains a handoff signal, runs ADAAgent next.
- Combines responses for a complete user answer.
"""

from .oka_agent import OKAAgent
from .ada_agent import ADAAgent


class AgentManager:
    def __init__(self):
        self.oka_agent = OKAAgent()
        self.ada_agent = ADAAgent()

    def handle_request(self, user_input: str) -> str:
        """
        Full orchestration flow:
        - Call OKAAgent to process input.
        - If handoff keyword detected, call ADAAgent too.
        - Return combined workflow steps.
        """
        oka_output = self.oka_agent.handle(user_input)

        # Detect handoff signal
        handoff_keywords = ["handoff to ada", "ready to finalize", "finalize lease"]
        if any(keyword in oka_output.lower() for keyword in handoff_keywords):
            ada_output = self.ada_agent.handle(user_input)
            final_response = (
                f"🤝 AgentManager Workflow:\n\n"
                f"=== OKAAgent ===\n{oka_output}\n\n"
                f"=== ADAAgent ===\n{ada_output}"
            )
        else:
            final_response = (
                f"🤝 AgentManager Workflow:\n\n"
                f"=== OKAAgent ===\n{oka_output}\n\n"
                f"(No ADA handoff triggered.)"
            )

        return final_response
