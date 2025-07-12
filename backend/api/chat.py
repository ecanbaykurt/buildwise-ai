# backend/api/chat.py

from fastapi import APIRouter
from pydantic import BaseModel
from backend.core.orchestrator import Orchestrator

router = APIRouter()

orchestrator = Orchestrator()

class ChatRequest(BaseModel):
    user_message: str
    user_id: str
    has_lease: bool

@router.post("/chat")
def chat_endpoint(req: ChatRequest):
    response = orchestrator.run(
        user_message=req.user_message,
        user_id=req.user_id,
        has_lease=req.has_lease
    )
    return {"response": response}
