"""
Orchestrator:
- Accepts raw user input from Streamlit or FastAPI.
- Logs input embedding to Pinecone (optional RAG).
- Uses OpenAI embeddings for semantic enrichment.
- Delegates main processing to AgentManager (OKA + ADA flow).
- Logs response embedding for memory or search.
- Returns structured final answer to the front-end.
"""

import uuid

# ✅ Always use absolute imports for safe Cloud deployment
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
        1. Create embedding for user input.
        2. Store input in Pinecone (optional).
        3. Run AgentManager (OKA → ADA if needed).
        4. Create embedding for agent response.
        5. Store response in Pinecone (optional).
        6. Return final structured response.
        """

        # ✅ Step 1: Embed user query
        embedding = self.client.embeddings.create(
            model="text-embedding-3-large",
            input=user_input
        ).data[0].embedding

        # ✅ Step 2: Save query embedding
        upsert_vector(
            vector_id=str(uuid.uuid4()),   # unique ID for this input
            embedding=embedding,
            metadata={
                "type": "user_input",
                "query": user_input
            }
        )

        # ✅ Step 3: Run full AgentManager flow
        agent_response = self.agent_manager.handle_request(user_input)

        # ✅ Step 4: Embed the agent response
        response_embedding = self.client.embeddings.create(
            model="text-embedding-3-large",
            input=agent_response
        ).data[0].embedding

        # ✅ Step 5: Save response embedding
        upsert_vector(
            vector_id=str(uuid.uuid4()),   # unique ID for this response
            embedding=response_embedding,
            metadata={
                "type": "agent_response",
                "answer": agent_response
            }
        )

        # ✅ Step 6: Return final output
        return agent_response
