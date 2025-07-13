import os
import pinecone

# ✅ Read your keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")

# ✅ NEW: create Pinecone client object
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

# ✅ You don’t need pinecone.init — you use `pc` now
index = pc.Index("your-index-name")

def upsert_vector(embedding, metadata):
    index.upsert(
        vectors=[("unique-id", embedding)],
        metadata=metadata
    )

def query_vector(embedding, top_k=1):
    return index.query(vector=embedding, top_k=top_k, include_metadata=True)
