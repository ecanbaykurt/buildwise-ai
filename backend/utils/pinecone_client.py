# backend/utils/pinecone_client.py

import pinecone
import os

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
index = pinecone.Index(PINECONE_INDEX)

def query_vector(query_embedding: list, top_k=3):
    return index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
