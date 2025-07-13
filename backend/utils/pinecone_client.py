import os
import pinecone

# ✅ Read your env variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

# ✅ Initialize new Pinecone v3 client
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

# ✅ Check if the index exists — create it if not
indexes = pc.list_indexes()
if PINECONE_INDEX not in indexes:
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=1536,   # or whatever dimension your embeddings use!
        metric="cosine"
    )

index = pc.Index(PINECONE_INDEX)

def upsert_vector(embedding, metadata):
    index.upsert(
        vectors=[("unique-id", embedding)],
        metadata=metadata
    )

def query_vector(embedding, top_k=1):
    return index.query(vector=embedding, top_k=top_k, include_metadata=True)
