from backend.utils.pinecone_client import query_vector
from openai import OpenAI

client = OpenAI()

class ActionAgent:
    def create_followup(self, user_message: str) -> str:
        embedding = client.embeddings.create(
            model="text-embedding-3-large",
            input=user_message
        ).data[0].embedding

        results = query_vector(embedding, top_k=1)
        if results.matches:
            return f"✅ Action Agent: Logging this lead for follow-up.\nSummary: {results.matches[0].metadata.get('summary', '')}"
        return "Action Agent: Nothing to record yet."
