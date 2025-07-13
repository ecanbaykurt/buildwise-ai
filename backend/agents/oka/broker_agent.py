# backend/agents/oka/broker_agent.py

from backend.utils.pinecone_client import query_vector
from openai import OpenAI

client = OpenAI()

class BrokerAgent:
    def __init__(self):
        pass

    def ask_neighborhood_info(self, question: str) -> str:
        embedding = client.embeddings.create(
            model="text-embedding-3-large",
            input=question
        ).data[0].embedding

        rag_result = query_vector(embedding, top_k=1)
        if rag_result.matches:
            return f"Here's what I found: {rag_result.matches[0].metadata.get('summary')}"
        return "I couldn't find information on that. Could you clarify?"
