# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging

# Optional: support both pinecone v3 (recommended) and legacy v2
try:
    from pinecone import Pinecone, ServerlessSpec  # v3
    PC_VERSION = 3
except Exception:
    PC_VERSION = 2
    import pinecone  # v2

# Routers
from backend.api import chat, upload
from backend.api.via import router as via_router
from backend.api.doma import router as doma_router

# Load env
load_dotenv()

# Logger
logger = logging.getLogger("buildwise")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def _env_ok(var: str, required: bool = True) -> bool:
    val = os.getenv(var)
    status = "OK" if val and len(val) > 8 else "MISSING"
    logger.info(f"{var}: {status}")
    if required and not val:
        return False
    return True

# Check critical env
required_ok = True
required_ok &= _env_ok("OPENAI_API_KEY", required=True)
required_ok &= _env_ok("PINECONE_API_KEY", required=True)
# Name can be PINECONE_INDEX or PINECONE_INDEX_NAME, support both
index_name = os.getenv("PINECONE_INDEX_NAME") or os.getenv("PINECONE_INDEX")
if not index_name:
    logger.warning("PINECONE_INDEX_NAME not set. Using default 'buildwise-index'")
    index_name = "buildwise-index"
region = os.getenv("PINECONE_REGION") or os.getenv("PINECONE_ENVIRONMENT") or "us-east-1"

if not required_ok:
    raise RuntimeError("Missing required environment variables. See logs above.")

# Create app
app = FastAPI(title="BuildWise AI", version="0.2.0")

# CORS for local dev and Streamlit
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pinecone init on startup
@app.on_event("startup")
def startup_index_init():
    try:
        if PC_VERSION == 3:
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            existing = {idx["name"] for idx in pc.list_indexes()}
            if index_name not in existing:
                logger.info(f"Creating Pinecone index '{index_name}' (v3 serverless)...")
                pc.create_index(
                    name=index_name,
                    dimension=1536,            # text-embedding-3-large
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region=region),
                )
            else:
                logger.info(f"Pinecone index '{index_name}' already exists.")
        else:
            pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=region)
            existing = pinecone.list_indexes()
            if index_name not in existing:
                logger.info(f"Creating Pinecone index '{index_name}' (v2)...")
                pinecone.create_index(name=index_name, dimension=1536, metric="cosine")
            else:
                logger.info(f"Pinecone index '{index_name}' already exists.")
    except Exception as e:
        logger.error(f"Pinecone init failed: {e}")
        raise

# Include routers
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(via_router)
app.include_router(doma_router)

# Health
@app.get("/")
def root():
    return {"message": "BuildWise AI is running", "pinecone_index": index_name, "region": region}

@app.get("/health")
def health():
    return {"status": "ok"}
