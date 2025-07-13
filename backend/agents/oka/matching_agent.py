from backend.utils.pinecone_client import query_vector
from openai import OpenAI

client = OpenAI()

class MatchingAgent:
    def rank_properties(self, preferences: str) -> str:
        embedding = client.embeddings.create(
            model="text-embedding-3-large",
            input=preferences
        ).data[0].embedding

        results = query_vector(embedding, top_k=3)
        matches = []
        for match in results.matches:
            m = match.metadata
            matches.append(f"🏢 {m.get('address')} | {m.get('unit_details', '')}")

        return "🏷️ Top Matches:\n" + "\n".join(matches) if matches else "No matches found."
