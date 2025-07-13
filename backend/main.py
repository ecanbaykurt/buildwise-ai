# backend/main.py

from fastapi import FastAPI
from backend.api import chat, upload
from dotenv import load_dotenv
import os
import pinecone
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Debug helper for env variables (never prints full secret)
def print_env_status(var):
    value = os.getenv(var)
    if value and len(value) > 8:
        print(f"{var}: ✅ Loaded")
    else:
        print(f"{var}: ❌ MISSING!")

print_env_status("OPENAI_API_KEY")
print_env_status("PINECONE_INDEX")
print_env_status("PINECONE_ENVIRONMENT")
print_env_status("PINECONE_API_KEY")

# Optionally, fail fast if critical env vars are missing
assert os.getenv("OPENAI_API_KEY"), "❌ OPENAI_API_KEY not set in environment!"
assert os.getenv("PINECONE_API_KEY"), "❌ PINECONE_API_KEY not set in environment!"

# Initialize FastAPI app
app = FastAPI()

# Include routers for modular endpoints
app.include_router(chat.router)
app.include_router(upload.router)

# Root health check endpoint
@app.get("/")
def read_root():
    return {"message": "Buildwise AI is running! 🚀"}
