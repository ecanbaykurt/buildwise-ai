from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import numpy as np

class MatchItem(BaseModel):
    id: str
    score: float
    reasons: List[str]
    missing_criteria: List[str] = []
    relaxed_field: Optional[str] = None
    row_preview: Dict[str, Any] = {}

class MatchResult(BaseModel):
    matches: List[MatchItem]
    spec_used: Dict[str, Any]

class MatchRankAgent:
    """
    Hybrid ranking placeholder.
    In production, replace with pgvector or Pinecone similarity + rules.
    """
    def __init__(self, inventory_rows: List[Dict[str, Any]]):
        self.inventory = inventory_rows

    def _hard_filter(self, row: Dict[str, Any], spec: Dict[str, Any]) -> bool:
        musts = {m.lower() for m in spec.get("must_haves", [])}
        amenities = {a.lower() for a in row.get("amenities", [])}
        return musts.issubset(amenities) if musts else True

    def _score(self, row: Dict[str, Any], spec: Dict[str, Any]) -> float:
        s = 0.0
        if spec.get("min_sqft") and row.get("sqft"):
            if row["sqft"] >= spec["min_sqft"]:
                s += 20
        if spec.get("max_sqft") and row.get("sqft"):
            if row["sqft"] <= spec["max_sqft"]:
                s += 20
        if spec.get("budget_monthly_usd") and row.get("rent"):
            b = spec["budget_monthly_usd"]
            lo, hi = b.get("min"), b.get("max")
            if lo is not None and row["rent"] >= lo:
                s += 15
            if hi is not None and row["rent"] <= hi:
                s += 15
        if spec.get("location") and row.get("neighborhood"):
            if any(loc.lower() in row["neighborhood"].lower() for loc in spec["location"]):
                s += 20
        return float(np.clip(s, 0, 100))

    def run(self, spec: Dict[str, Any], topn: int = 5) -> MatchResult:
        candidates = []
        for row in self.inventory:
            if not self._hard_filter(row, spec):
                continue
            score = self._score(row, spec)
            reasons = []
            if row.get("neighborhood"):
                reasons.append(f"Neighborhood match {row['neighborhood']}")
            if row.get("sqft"):
                reasons.append(f"{row['sqft']} sqft fits range")
            if row.get("rent"):
                reasons.append(f"Rent ${row['rent']} within budget")
            candidates.append(MatchItem(
                id=str(row.get("id", "")),
                score=score,
                reasons=reasons[:3],
                row_preview=row
            ))
        candidates.sort(key=lambda x: x.score, reverse=True)
        # constraint relaxation if few results
        relaxed = None
        if len(candidates) < 3:
            if spec.get("max_sqft"):
                spec["max_sqft"] = int(spec["max_sqft"] * 1.1)
                relaxed = "max_sqft"
        for c in candidates:
            c.relaxed_field = relaxed
        return MatchResult(matches=candidates[:topn], spec_used=spec)
