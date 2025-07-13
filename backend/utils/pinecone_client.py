import pinecone  # ✅ not pinecone-client

import os

# Init Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")  # optional if you have env

pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

index = pinecone.Index("your-index-name")

def upsert_vector(embedding, metadata):
    index.upsert(
        vectors=[("unique-id", embedding)],
        metadata=metadata
    )

def query_vector(embedding, top_k=1):
    return index.query(vector=embedding, top_k=top_k, include_metadata=True)
