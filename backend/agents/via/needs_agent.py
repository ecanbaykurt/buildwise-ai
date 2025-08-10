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
    def run(self, user_text: str, sample_rows: Optional[str]) -> SearchSpec:
        msgs = [{"role": "system", "content": VIA_SYSTEM}]
        ctx = f"User says: {user_text}"
        if sample_rows:
            ctx += f"\nSample inventory rows:\n{sample_rows}"
        msgs.append({"role": "user", "content": ctx})

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=msgs,
            response_format={"type": "json_object"}  # hint, but still not guaranteed
        )
        raw = resp.choices[0].message.content

        # --- SAFE PARSE + COERCE ---
        import json
        def _coerce_spec(d: dict) -> dict:
            # normalize types the model often messes up
            d = dict(d or {})
            # location
            loc = d.get("location")
            if isinstance(loc, str): d["location"] = [loc]
            elif not isinstance(loc, list): d["location"] = []
            # budget
            b = d.get("budget_monthly_usd")
            if isinstance(b, (int, float, str)):
                # treat as max
                try:
                    d["budget_monthly_usd"] = {"min": None, "max": float(b)}
                except Exception:
                    d["budget_monthly_usd"] = None
            elif isinstance(b, dict):
                # coerce values
                for k in ("min", "max"):
                    if k in b and b[k] is not None:
                        try: b[k] = float(b[k])
                        except Exception: b[k] = None
                d["budget_monthly_usd"] = {"min": b.get("min"), "max": b.get("max")}
            else:
                d["budget_monthly_usd"] = None
            # must/nice to haves
            for k in ("must_haves", "nice_to_haves"):
                v = d.get(k)
                if isinstance(v, str): d[k] = [v]
                elif not isinstance(v, list): d[k] = []
            # ints
            for k in ("min_sqft", "max_sqft", "term_months"):
                if k in d and d[k] is not None:
                    try: d[k] = int(float(d[k]))
                    except Exception: d[k] = None
            # confidence map
            if not isinstance(d.get("confidence"), dict):
                d["confidence"] = {}
            # status
            if d.get("spec_status") not in ("ok", "underconstrained"):
                d["spec_status"] = "ok"
            return d

        try:
            data = json.loads(raw)                # don’t trust validator yet
            data = _coerce_spec(data)
            return SearchSpec(**data)             # pydantic validate AFTER coercion
        except Exception:
            # graceful fallback so the app keeps running
            return SearchSpec(
                location=[],
                budget_monthly_usd=None,
                term_months=None,
                must_haves=[],
                nice_to_haves=[],
                timeline=None,
                use_case=None,
                confidence={},
                spec_status="underconstrained",
            )
