from backend.utils.pinecone_client import query_vector
from openai import OpenAI

client = OpenAI()

class CRM_Agent:
    def log_agreement(self, question: str) -> str:
        embedding = client.embeddings.create(
            model="text-embedding-3-large",
            input=question
        ).data[0].embedding

        results = query_vector(embedding, top_k=1)
        if results.matches:
            return f"🗂️ CRM Agent: Updated CRM with — {results.matches[0].metadata.get('summary', '')}"
        return "CRM Agent: No CRM update needed for that."
