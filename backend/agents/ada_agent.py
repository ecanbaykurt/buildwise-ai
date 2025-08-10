# backend/agents/ada_agent.py

"""
ADAAgent: Finalizes the leasing process by chaining:
1. LeaseAgent: Clarifies lease terms and conditions.
2. CRMAgent: Logs user agreement details into CRM.
3. DecisionAgent: Provides negotiation support or final decision steps.
"""

class LeaseAgent:
    """
    LeaseAgent: Explains lease details and answers contract-related questions.
    """
    def run(self, user_input: str) -> str:
        prompt = (
            "You are a professional leasing consultant. Review the user request "
            "and explain the relevant lease terms clearly. Highlight any conditions, "
            "penalties, renewal options, and responsibilities.\n\n"
            f"User says: '{user_input}'"
        )

        # Example placeholder response:
        lease_terms = (
            "The standard lease is for 12 months, renewable with a 3% increase. "
            "Security deposit equals one month’s rent. Early termination incurs a 2-month penalty."
        )
        return lease_terms


class CRMAgent:
    """
    CRMAgent: Logs agreement details and updates customer records.
    """
    def run(self, lease_summary: str) -> str:
        prompt = (
            "As a CRM Agent, generate a clear CRM log entry based on the lease details. "
            "Summarize any commitments, agreements, or next follow-up actions.\n\n"
            f"Lease Summary: '{lease_summary}'"
        )

        # Example placeholder:
        crm_entry = (
            "CRM Update: User agreed to 12-month lease, deposit confirmed. "
            "Next action: Send lease draft for e-signature within 24 hours."
        )
        return crm_entry


class DecisionAgent:
    """
    DecisionAgent: Supports final negotiation and gives final decision.
    """
    def run(self, crm_entry: str) -> str:
        prompt = (
            "As a negotiation advisor, check if any negotiation is needed. "
            "If yes, suggest concessions or next steps. Otherwise, provide a clear closing statement.\n\n"
            f"CRM Entry: '{crm_entry}'"
        )

        # Example placeholder:
        decision = (
            "Decision: No further negotiation needed. Proceed to final signature. "
            "Handoff to property manager for keys and move-in instructions."
        )
        return decision


class ADAAgent:
    """
    ADAAgent: Coordinates Lease → CRM → Decision steps.
    """
    def __init__(self):
        self.lease_agent = LeaseAgent()
        self.crm_agent = CRMAgent()
        self.decision_agent = DecisionAgent()

    def handle(self, user_input: str) -> str:
        lease_output = self.lease_agent.run(user_input)
        crm_output = self.crm_agent.run(lease_output)
        decision_output = self.decision_agent.run(crm_output)

        return (
            f"ADA Agent Workflow:\n\n"
            f"LeaseAgent: {lease_output}\n\n"
            f"CRMAgent: {crm_output}\n\n"
            f"DecisionAgent: {decision_output}"
        )
