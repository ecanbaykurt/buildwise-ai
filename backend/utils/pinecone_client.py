import pinecone
import streamlit as st

# ✅ Load secrets from Streamlit Cloud
PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
PINECONE_INDEX = st.secrets["PINECONE_INDEX"]

# ✅ Init Pinecone client (v3)
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

# ✅ Check if index exists or create it
existing_indexes = [index.name for index in pc.list_indexes()]

if PINECONE_INDEX not in existing_indexes:
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=1536,     # Make sure this matches your embeddings dimension!
        metric="cosine",
        spec=pinecone.ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# ✅ Connect to the index
index = pc.Index(PINECONE_INDEX)

# ✅ Function to upsert a vector
def upsert_vector(vector_id: str, embedding: list[float], metadata: dict = None):
    """
    Upserts a single vector into Pinecone.
    """
    vectors = [{
        "id": vector_id,
        "values": embedding,
        "metadata": metadata or {}
    }]
    index.upsert(vectors=vectors)

# ✅ Function to query a vector
def query_vector(embedding: list[float], top_k: int = 5, include_metadata: bool = True):
    """
    Queries Pinecone for the most similar vectors.
    """
    response = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=include_metadata
    )
    return response
