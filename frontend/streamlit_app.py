# frontend/streamlit_app.py

import sys
import os
import json
import uuid
import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from openai import OpenAI

# add project root for optional imports if you later split files
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# openai client
client = OpenAI()

# page config
st.set_page_config(
    page_title="BuildWise AI",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# minimal css
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None
if "mode" not in st.session_state:
    st.session_state.mode = "VIA"

# header
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;">
  <div style="width:36px;height:36px;border-radius:8px;background:#6c5ce7;color:white;display:flex;align-items:center;justify-content:center;font-weight:700;">B</div>
  <div>
    <h2 style="margin:0;">BuildWise AI</h2>
    <p style="margin:0;opacity:0.8;">Property management and real estate analytics assistant</p>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# file uploader
st.subheader("Upload your dataset CSV")
uploaded_file = st.file_uploader("Upload CSV with listings such as id, address, neighborhood, sqft, rent, amenities", type="csv")
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state.uploaded_df = df
        st.success(f"Loaded {uploaded_file.name} with {len(df)} rows")
        st.dataframe(df.head(10), use_container_width=True)
    except Exception as e:
        st.error(f"Error reading file: {e}")

# mode selection
col_a, col_b = st.columns(2)
with col_a:
    st.session_state.mode = st.radio(
        "Choose pipeline",
        options=["VIA", "DOMA"],
        format_func=lambda x: "VIA  new tenant" if x == "VIA" else "DOMA  existing tenant",
        horizontal=True
    )

with col_b:
    if st.session_state.mode == "VIA":
        st.info("VIA will extract needs, rank matches, and propose tours")
    else:
        st.info("DOMA supports lease questions, service triage, and renewal offers")

# simple calendar slots for demo
DEFAULT_SLOTS = [
    {"start": "2025-08-12T15:30:00Z", "end": "2025-08-12T16:00:00Z"},
    {"start": "2025-08-13T14:00:00Z", "end": "2025-08-13T14:30:00Z"},
]

# =========================
# VIA agents inline
# =========================

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
    spec_status: str = "ok"

VIA_SYSTEM = (
    "You are a real estate intake specialist. Extract a complete search spec as JSON. "
    "Infer cautiously. Include a confidence 0 to 1 per field. "
    "If budget is implausibly low for the given area, set spec_status to 'underconstrained' and suggest adjustments."
)

class NeedsAgent:
    def run(self, user_text: str, sample_rows: Optional[str] = None) -> SearchSpec:
        messages = [{"role": "system", "content": VIA_SYSTEM}]
        context = f"User says: {user_text}"
        if sample_rows:
            context += f"\nSample inventory rows:\n{sample_rows}"
        messages.append({"role": "user", "content": context})

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"}
        )
        data = resp.choices[0].message.content
        return SearchSpec.model_validate_json(data)

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
    def __init__(self, inventory_rows: List[Dict[str, Any]]):
        self.inventory = inventory_rows

    def _hard_filter(self, row: Dict[str, Any], spec: Dict[str, Any]) -> bool:
        musts = {m.lower() for m in spec.get("must_haves", [])}
        amenities = {a.lower() for a in row.get("amenities", [])} if isinstance(row.get("amenities"), list) else set()
        return musts.issubset(amenities) if musts else True

    def _score(self, row: Dict[str, Any], spec: Dict[str, Any]) -> float:
        s = 0.0
        if spec.get("min_sqft") and row.get("sqft"):
            if row["sqft"] >= spec["min_sqft"]:
                s += 20
        if spec.get("max_sqft") and row.get("sqft"):
            if row["sqft"] <= spec["max_sqft"]:
                s += 20
        if spec.get("budget_monthly_usd") and row.get("rent") is not None:
            b = spec["budget_monthly_usd"]
            lo, hi = b.get("min"), b.get("max")
            if lo is not None and row["rent"] >= lo:
                s += 15
            if hi is not None and row["rent"] <= hi:
                s += 15
        if spec.get("location") and row.get("neighborhood"):
            if any(loc.lower() in str(row["neighborhood"]).lower() for loc in spec["location"]):
                s += 20
        return min(100.0, max(0.0, s))

    def run(self, spec: Dict[str, Any], topn: int = 5) -> MatchResult:
        candidates: List[MatchItem] = []
        for row in self.inventory:
            if not self._hard_filter(row, spec):
                continue
            score = self._score(row, spec)
            reasons = []
            if row.get("neighborhood"):
                reasons.append(f"Neighborhood match {row['neighborhood']}")
            if row.get("sqft"):
                reasons.append(f"{row['sqft']} sqft fits range")
            if row.get("rent") is not None:
                reasons.append(f"Rent ${row['rent']} within budget")
            candidates.append(MatchItem(
                id=str(row.get("id", row.get("address", ""))),
                score=score,
                reasons=reasons[:3],
                row_preview=row
            ))
        candidates.sort(key=lambda x: x.score, reverse=True)
        relaxed = None
        if len(candidates) < 3 and spec.get("max_sqft"):
            spec["max_sqft"] = int(spec["max_sqft"] * 1.1)
            relaxed = "max_sqft"
        for c in candidates:
            c.relaxed_field = relaxed
        return MatchResult(matches=candidates[:topn], spec_used=spec)

class ActionPlan(BaseModel):
    actions: List[Dict[str, Any]]
    confirmation_prompt: str

class TourCloseAgent:
    def __init__(self, calendar_slots: List[Dict[str, str]]):
        self.slots = calendar_slots

    def run(self, matches: List[Dict[str, Any]]) -> ActionPlan:
        proposals = []
        for m in matches[:2]:
            slot = self.slots[0] if self.slots else {"start": "2025-08-12T15:30:00Z", "end": "2025-08-12T16:00:00Z"}
            proposals.append({
                "type": "tour",
                "unit_id": m.get("id"),
                "address": m.get("row_preview", {}).get("address", ""),
                "start": slot["start"],
                "end": slot["end"],
                "required_docs": ["photo_id", "income_proof"]
            })
        confirm = "Would you like me to book the first tour, the second tour, or propose other times"
        return ActionPlan(actions=proposals, confirmation_prompt=confirm)

class VIAAgent:
    def __init__(self, inventory_rows: List[Dict[str, Any]], calendar_slots: List[Dict[str, str]]):
        self.inventory = inventory_rows
        self.calendar = calendar_slots
        self.needs = NeedsAgent()
        self.closer = TourCloseAgent(calendar_slots)

    def handle(self, user_text: str, sample_rows: Optional[str] = None) -> Dict[str, Any]:
        spec = self.needs.run(user_text=user_text, sample_rows=sample_rows)
        matcher = MatchRankAgent(inventory_rows=self.inventory)
        mres = matcher.run(spec=spec.model_dump())
        plan = self.closer.run([m.model_dump() for m in mres.matches])
        return {
            "stage": "VIA",
            "search_spec": spec.model_dump(),
            "matches": [m.model_dump() for m in mres.matches],
            "action_plan": plan.model_dump()
        }

# =========================
# DOMA agents inline
# =========================

DOMA_SYSTEM = (
    "You answer strictly from retrieved lease text. Cite section or page. "
    "If the answer is not in the text, say Not found in provided lease and suggest escalation."
)

class LeaseAnswer(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    risk_flags: List[str] = []

class LeaseQAAgent:
    def run(self, question: str, retrieved_chunks: List[Dict[str, Any]]) -> LeaseAnswer:
        context = "\n\n".join([f"[{c.get('source','doc')} p{c.get('page','?')}] {c.get('text','')}" for c in retrieved_chunks])
        messages = [
            {"role": "system", "content": DOMA_SYSTEM},
            {"role": "user", "content": f"Lease snippets:\n{context}\n\nQuestion: {question}\nProvide a concise answer with inline citations"}
        ]
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        txt = resp.choices[0].message.content
        cits = [{"section": "unknown", "page": c.get("page")} for c in retrieved_chunks[:2]]
        return LeaseAnswer(answer=txt, citations=cits)

class TriageResult(BaseModel):
    category: str
    priority: str
    vendor: str
    eta_hours: int
    confirm_message: str

EMERGENCY_KEYWORDS = {"gas leak", "water main break", "sparks", "smoke"}

class ServiceTriageAgent:
    def run(self, ticket_text: str, photos: Optional[List[str]] = None) -> TriageResult:
        text_low = ticket_text.lower()
        if any(k in text_low for k in EMERGENCY_KEYWORDS):
            return TriageResult(
                category="emergency",
                priority="P0",
                vendor="dispatch_call_center",
                eta_hours=1,
                confirm_message="Emergency detected. We are dispatching immediately. Please evacuate if unsafe and call local emergency services."
            )
        category = "plumbing" if "leak" in text_low else "hvac" if ("ac" in text_low or "air" in text_low) else "general"
        vendor = "preferred_plumber_inc" if category == "plumbing" else "preferred_hvac_llc" if category == "hvac" else "handyman_pool"
        eta = 24 if category == "general" else 8
        return TriageResult(
            category=category, priority="P2", vendor=vendor, eta_hours=eta,
            confirm_message=f"Ticket logged as {category}. Assigned {vendor}. Estimated visit within {eta} hours."
        )

class Offer(BaseModel):
    rent_usd: float
    term_months: int
    incentives: List[str] = []

class RenewalPackage(BaseModel):
    primary: Offer
    alternatives: List[Offer]
    justification: str
    needs_manager_approval: bool = False

class RenewalDealAgent:
    def run(self, current_rent: float, comps_median: float, policy_floor: float, policy_ceiling: float) -> RenewalPackage:
        target = max(policy_floor, min(comps_median, policy_ceiling))
        primary = Offer(rent_usd=target, term_months=12, incentives=["touch up paint"])
        alt1 = Offer(rent_usd=target * 0.98, term_months=24, incentives=["one month free at end"])
        alt2 = Offer(rent_usd=target * 1.01, term_months=12, incentives=["new appliance package"])
        approval = not (policy_floor <= primary.rent_usd <= policy_ceiling)
        just = f"Priced near market median ${comps_median:.0f}, within policy [{policy_floor:.0f}, {policy_ceiling:.0f}]"
        return RenewalPackage(primary=primary, alternatives=[alt1, alt2], justification=just, needs_manager_approval=approval)

# =========================
# UI logic
# =========================

st.markdown("---")

if st.session_state.mode == "VIA":
    st.subheader("VIA  new tenant acquisition")
    user_text = st.text_input("Describe the space you want", placeholder="Example  Midtown office 1000 to 1200 sqft under 4500 per month pet friendly")
    run_btn = st.button("Run VIA")
    if run_btn:
        if st.session_state.uploaded_df is None or st.session_state.uploaded_df.empty:
            st.warning("Please upload a dataset before running VIA")
        else:
            df = st.session_state.uploaded_df.copy()
            # normalize amenities column into list when possible
            if "amenities" in df.columns and df["amenities"].dtype == object:
                def to_list(v):
                    if isinstance(v, list):
                        return v
                    try:
                        return json.loads(v)
                    except Exception:
                        return [str(v)]
                df["amenities"] = df["amenities"].apply(to_list)
            inventory = df.to_dict(orient="records")
            sample_rows = df.head(3).to_string()
            via = VIAAgent(inventory_rows=inventory, calendar_slots=DEFAULT_SLOTS)
            with st.spinner("Extracting needs, ranking matches, and drafting tour plan"):
                result = via.handle(user_text=user_text, sample_rows=sample_rows)
            st.success("VIA completed")
            st.json(result)

else:
    st.subheader("DOMA  existing tenant operations")
    doma_tab = st.tabs(["Lease Q and A", "Service triage", "Renewal offer"])[0]

    tab1, tab2, tab3 = st.tabs(["Lease Q and A", "Service triage", "Renewal offer"])

    with tab1:
        question = st.text_input("Ask about your lease", placeholder="When is my renewal notice due")
        lease_text = st.text_area("Paste lease excerpts or notes", height=180, placeholder="Paste relevant clauses here")
        ask_btn = st.button("Answer from lease")
        if ask_btn:
            chunks = []
            if lease_text.strip():
                # simple fake chunking for demo
                for i, block in enumerate(lease_text.split("\n\n")):
                    chunks.append({"source": "lease", "page": i + 1, "text": block[:1200]})
            agent = LeaseQAAgent()
            with st.spinner("Answering from provided lease text"):
                ans = agent.run(question=question, retrieved_chunks=chunks)
            st.json(ans.model_dump())

    with tab2:
        tx = st.text_area("Describe the issue", height=120, placeholder="Example  bathroom leak under sink since last night")
        triage_btn = st.button("Create service ticket")
        if triage_btn:
            triage = ServiceTriageAgent().run(ticket_text=tx)
            st.json(triage.model_dump())

    with tab3:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            current_rent = st.number_input("Current rent USD", min_value=0.0, value=3200.0, step=50.0)
        with col2:
            comps_median = st.number_input("Comps median USD", min_value=0.0, value=3300.0, step=50.0)
        with col3:
            policy_floor = st.number_input("Policy floor USD", min_value=0.0, value=3000.0, step=50.0)
        with col4:
            policy_ceiling = st.number_input("Policy ceiling USD", min_value=0.0, value=3600.0, step=50.0)
        renew_btn = st.button("Propose renewal package")
        if renew_btn:
            pkg = RenewalDealAgent().run(current_rent, comps_median, policy_floor, policy_ceiling)
            st.json(pkg.model_dump())

# optional chat history viewer
with st.expander("Session messages"):
    st.write(st.session_state.chat_history)

st.markdown("---")
st.markdown('<div style="text-align:center;color:#7f8c8d;padding:8px;">BuildWise AI  your AI assistant for real estate</div>', unsafe_allow_html=True)
