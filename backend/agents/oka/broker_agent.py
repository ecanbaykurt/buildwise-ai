from backend.utils.pinecone_client import query_vector
from openai import OpenAI

client = OpenAI()

class BrokerAgent:
    def handle(self, user_message: str) -> str:
        embedding = client.embeddings.create(
            model="text-embedding-3-large",
            input=user_message
        ).data[0].embedding

        results = query_vector(embedding, top_k=2)
        if results.matches:
            info = results.matches[0].metadata.get("summary", "No details.")
            return f"🔍 Broker Agent says:\n{info}"
        return "Broker Agent: Sorry, I found nothing for that."
