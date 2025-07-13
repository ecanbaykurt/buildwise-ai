from backend.utils.pinecone_client import query_vector
from openai import OpenAI

client = OpenAI()

class DecisionAgent:
    def support_negotiation(self, question: str) -> str:
        embedding = client.embeddings.create(
            model="text-embedding-3-large",
            input=question
        ).data[0].embedding

        results = query_vector(embedding, top_k=1)
        if results.matches:
            return f"💬 Decision Agent: Based on policy — {results.matches[0].metadata.get('summary', '')}"
        return "Decision Agent: I couldn’t find negotiation guidelines for that."
