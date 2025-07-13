# backend/agents/oka/matching_agent.py

from backend.utils.pinecone_client import query_vector
from openai import OpenAI

client = OpenAI()

class MatchingAgent:
    def __init__(self):
        pass

    def rank_properties(self, preferences: str) -> str:
        # 1️⃣ Embed the user query
        embedding = client.embeddings.create(
            model="text-embedding-3-large",
            input=preferences
        ).data[0].embedding

        # 2️⃣ Query Pinecone
        rag_result = query_vector(embedding, top_k=3)

        # 3️⃣ Format RAG output for user
        matches = []
        for match in rag_result.matches:
            metadata = match.metadata
            score = match.score
            matches.append(f"🏢 {metadata.get('address')} — Score: {round(score, 2)}")

        if not matches:
            return "Sorry, I couldn’t find any good matches."

        return f"Here are the top matches I found:\n" + "\n".join(matches)
