import pinecone
import streamlit as st

# ✅ Load secrets from Streamlit Cloud
PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
PINECONE_INDEX = st.secrets["PINECONE_INDEX"]

# ✅ Init Pinecone v3
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

# ✅ Check if index exists or create it
indexes = [index.name for index in pc.list_indexes()]

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

# ✅ Connect to the index
index = pc.Index(PINECONE_INDEX)

# ✅ ✅ ✅ These must exist so your import works!
def upsert_vector(embedding, metadata):
    index.upsert(
        vectors=[("unique-id", embedding)],
        metadata=metadata
    )

def query_vector(embedding, top_k=1):
    return index.query(vector=embedding, top_k=top_k, include_metadata=True)
