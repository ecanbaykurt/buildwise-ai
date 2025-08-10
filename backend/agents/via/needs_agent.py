from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from openai import OpenAI

client = OpenAI()

class SearchSpec(BaseModel):
    location: List[str] = Field(default_factory=list)
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None
    budget_monthly_usd: Optional[Dict[str, Optional[float]]] = None
    term_months: Optional[int] = None
    must_haves: List[str] = Field(default_factory=list)
    nice_to_haves: List[str] = Field(default_factory=list)
    timeline: Optional[str] = None
    use_case: Optional[str] = None
    confidence: Dict[str, float] = Field(default_factory=dict)
    spec_status: str = "ok"  # ok or underconstrained

SYSTEM_PROMPT = (
    "You are a real estate intake specialist. Extract a complete search spec as JSON. "
    "Infer cautiously. Include a confidence 0 to 1 per field. "
    "If budget is implausibly low for Manhattan or the given area, set spec_status to 'underconstrained' and suggest adjustments."
)

class NeedsAgent:
    def run(self, user_text: str, sample_rows: str | None = None) -> SearchSpec:
        messages = [{"role":"system","content":SYSTEM_PROMPT}]
        context = f"User says: {user_text}"
        if sample_rows:
            context += f"\nSample inventory rows:\n{sample_rows}"
        messages.append({"role":"user","content":context})

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type":"json_object"}
        )
        data = resp.choices[0].message.content
        return SearchSpec.model_validate_json(data)
