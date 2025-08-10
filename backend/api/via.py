from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from backend.agents.via.via_pipeline import VIAAgent
from backend.core.notifications import publish_event

router = APIRouter(prefix="/via", tags=["via"])

class ViaNeedsRequest(BaseModel):
    user_text: str
    sample_rows: Optional[str] = None
    inventory_rows: List[Dict[str, Any]] = []
    calendar_slots: List[Dict[str, str]] = []

@router.post("/run")
def via_run(req: ViaNeedsRequest):
    via = VIAAgent(inventory_rows=req.inventory_rows, calendar_slots=req.calendar_slots)
    out = via.handle(req.user_text, req.sample_rows)
    publish_event("via.pipeline.completed", {"matches": out.get("matches", [])}, actor="VIAAgent")
    return out
