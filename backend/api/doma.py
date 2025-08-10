from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from backend.agents.doma.doma_pipeline import DOMAAgent
from backend.core.notifications import publish_event

router = APIRouter(prefix="/doma", tags=["doma"])

class LeaseQARequest(BaseModel):
    question: str
    retrieved_chunks: List[Dict[str, Any]]

class TriageRequest(BaseModel):
    ticket_text: str
    photos: List[str] = []

class RenewalRequest(BaseModel):
    current_rent: float
    comps_median: float
    policy_floor: float
    policy_ceiling: float

doma = DOMAAgent()

@router.post("/lease-qa")
def lease_qa(req: LeaseQARequest):
    out = doma.handle_lease(req.question, req.retrieved_chunks)
    publish_event("doma.lease.answer", out, actor="LeaseQAAgent")
    return out

@router.post("/triage")
def triage(req: TriageRequest):
    out = doma.handle_triage(req.ticket_text, req.photos)
    publish_event("doma.triage.created", out, actor="ServiceTriageAgent")
    return out

@router.post("/renewal")
def renewal(req: RenewalRequest):
    out = doma.handle_renewal(req.current_rent, req.comps_median, req.policy_floor, req.policy_ceiling)
    publish_event("doma.renewal.offer", out, actor="RenewalDealAgent")
    return out
