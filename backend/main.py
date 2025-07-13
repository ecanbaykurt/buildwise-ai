# backend/main.py

from fastapi import FastAPI
from backend.api import chat, upload
from dotenv import load_dotenv
import os
import pinecone
import pandas as pd



# Load environment variables from .env file
load_dotenv()

# Optional debug to verify env variables are loaded correctly
print("✅ OpenAI Key:", os.getenv("OPENAI_API_KEY"))
print("✅ Pinecone Index:", os.getenv("PINECONE_INDEX"))
print("✅ Pinecone Environment:", os.getenv("PINECONE_ENVIRONMENT"))
print("PINECONE_API_KEY:", os.getenv("PINECONE_API_KEY"))

# Initialize FastAPI app
app = FastAPI()

# Include the chat router
app.include_router(chat.router)
app.include_router(upload.router)

# Root health check endpoint
@app.get("/")

def read_root():
    return {"message": "Buildwise AI is running! 🚀"}
