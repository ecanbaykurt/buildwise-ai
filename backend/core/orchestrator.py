# backend/core/orchestrator.py

import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from backend.agents.agent_manager import AgentManager

class Orchestrator:
    """
    Top-level orchestrator for Buildwise AI.
    Combines your RAG context + multi-agent routing.
    """

    def __init__(self):
        load_dotenv()

        # Load .env keys
        openai_key = os.getenv("OPENAI_API_KEY")
        pinecone_key = os.getenv("PINECONE_API_KEY")
        pinecone_index = os.getenv("PINECONE_INDEX")

        if not openai_key:
            raise ValueError("OPENAI_API_KEY not set!")
        if not pinecone_key:
            raise ValueError("PINECONE_API_KEY not set!")
        if not pinecone_index:
            raise ValueError("PINECONE_INDEX not set!")

        # Initialize clients
        self.openai_client = OpenAI(api_key=openai_key)
        self.pinecone_client = Pinecone(api_key=pinecone_key)
        self.index = self.pinecone_client.Index(pinecone_index)

        # ✅ Load your multi-agent manager
        self.manager = AgentManager()

    def embed_query(self, query: str) -> list:
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        return response.data[0].embedding

    def retrieve_context(self, query: str, top_k: int = 5) -> str:
        embedded_query = self.embed_query(query)
        response = self.index.query(
            vector=embedded_query,
            top_k=top_k,
            include_metadata=True
        )
        contexts = [
            match["metadata"]["text"]
            for match in response["matches"]
            if "metadata" in match and "text" in match["metadata"]
        ]
        return "\n".join(contexts)

    def run(self, user_message: str, user_id: str, has_lease: bool) -> str:
        """
        Main entry point.
        1) Retrieve extra RAG context
        2) Let OKA or ADA handle it using the Agent Manager
        """
        print(f"[Orchestrator] Running for user: {user_id} | Has lease: {has_lease}")

        # Step 1: Get context from Pinecone RAG
        rag_context = self.retrieve_context(user_message)
        print(f"[Orchestrator] Retrieved RAG context: {rag_context}")

        # Optional: Combine user message + context if you want to pass all
        combined_message = f"{rag_context}\n{user_message}"

        # Step 2: Route to the right agent flow
        answer = self.manager.route_request(
            user_message=combined_message,
            user_id=user_id,
            has_lease=has_lease
        )

        return answer
