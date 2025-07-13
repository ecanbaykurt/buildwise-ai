import os
import pinecone
import streamlit as st

PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
PINECONE_INDEX = st.secrets["PINECONE_INDEX"]

# New v3 client
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

# Get index list
indexes = [index.name for index in pc.list_indexes()]

if PINECONE_INDEX not in indexes:
    print(f"✅ Index '{PINECONE_INDEX}' does not exist. Creating...")
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=1536,
        metric="cosine",
        spec=pinecone.ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
else:
    print(f"✅ Index '{PINECONE_INDEX}' already exists — skipping creation.")

index = pc.Index(PINECONE_INDEX)
