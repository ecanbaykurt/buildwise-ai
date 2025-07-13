# backend/orchestrator.py

"""
Orchestrator:
- Accepts raw user input from your front-end or FastAPI.
- Optionally logs input/query to Pinecone for RAG.
- Uses OpenAI embeddings for semantic enrichment if needed.
- Delegates all request handling to AgentManager.
- Returns structured final response for the user.
"""

from backend.agents.agent_manager import AgentManager
from backend.utils.pinecone_client import upsert_vector, query_vector
from openai import OpenAI

class Orchestrator:
    def __init__(self):
        self.agent_manager = AgentManager()
        self.client = OpenAI()

    def handle_chat_request(self, user_input: str) -> str:
        """
        Orchestrator Flow:
        1. Log user query embedding to Pinecone (optional).
        2. Call AgentManager for multi-agent processing.
        3. Log the response embedding (optional).
        4. Return final combined output.
        """

        # Step 1: Embed query for logging or semantic search
        embedding = self.client.embeddings.create(
            model="text-embedding-3-large",
            input=user_input
        ).data[0].embedding

        # Optional: Save embedding with metadata
        upsert_vector(
            embedding=embedding,
            metadata={"type": "user_input", "query": user_input}
        )

        # Step 2: Run AgentManager workflow
        agent_response = self.agent_manager.handle_request(user_input)

        # Step 3: (Optional) Log final answer back to Pinecone
        response_embedding = self.client.embeddings.create(
            model="text-embedding-3-large",
            input=agent_response
        ).data[0].embedding

        upsert_vector(
            embedding=response_embedding,
            metadata={"type": "agent_response", "answer": agent_response}
        )

        # Step 4: Return final response for Streamlit
        return agent_response
