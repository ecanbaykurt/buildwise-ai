import pinecone
import streamlit as st  # for secrets in Streamlit Cloud

# ✅ Load secrets
PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
PINECONE_INDEX = st.secrets["PINECONE_INDEX"]

# ✅ New v3 client
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

# ✅ Check or create
indexes = pc.list_indexes()
if PINECONE_INDEX not in indexes:
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=1536,
        metric="cosine",
        spec=pinecone.ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

index = pc.Index(PINECONE_INDEX)

def upsert_vector(embedding, metadata):
    index.upsert(
        vectors=[("unique-id", embedding)],
        metadata=metadata
    )

def query_vector(embedding, top_k=1):
    return index.query(vector=embedding, top_k=top_k, include_metadata=True)
