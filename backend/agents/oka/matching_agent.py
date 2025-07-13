from backend.loaders.csv_excel_loader import load_building_data, load_unit_data
from backend.utils.pinecone_client import query_vector

import openai  # or your embedding model
import os

# Setup OpenAI embedding
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

class MatchingAgent:
    def __init__(self):
        self.buildings = load_building_data()
        self.units = load_unit_data()

    def find_matches(self, preferences: dict) -> list:
        """
        Combines keyword filter + Pinecone RAG
        """
        # 1️⃣ Filter by budget or location
        df = self.units

        if "budget" in preferences:
            df = df[df['price'] <= preferences['budget']]

        if "location" in preferences:
            df = df[df['location'].str.contains(preferences['location'], case=False)]

        # 2️⃣ Embed client needs
        description = f"Find best units for: {preferences}"
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=description
        )
        query_embedding = response.data[0].embedding

        # 3️⃣ Query Pinecone index
        rag_response = query_vector(query_embedding)

        # 4️⃣ Combine both if needed
        top_matches = rag_response.matches

        return top_matches
