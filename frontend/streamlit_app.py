# frontend/streamlit_app.py
import os, sys, json, uuid
from typing import List, Dict, Any, Optional
import pandas as pd
import streamlit as st
from pydantic import BaseModel, Field
from openai import OpenAI

# allow future local imports if you split files
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

client = OpenAI()

# ---------- Page ----------
st.set_page_config(
    page_title="BuildWise AI — VIA & DOMA (Manager)",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styles ----------
st.markdown("""
<style>
#MainMenu, header, footer {visibility:hidden;}
.block-container { padding-top: 1.2rem; padding-bottom: 1.2rem; }
.chat-bubble { padding: 12px 14px; border-radius: 14px; margin: 6px 0; }
.user-bubble { background: #eef2ff; border: 1px solid #e0e7ff; }
.assistant-bubble { background: #f9fafb; border: 1px solid #e5e7eb; }
.card { border:1px solid #e5e7eb; background:#fff; border-radius:14px; padding:14px; }
hr.soft { border:none; border-top:1px solid #eee; margin:12px 0; }
.suggestion-chip { display:inline-block; padding:6px 10px; border-radius:999px; border:1px solid #e0e7ff; background:#eef2ff; margin:4px 6px 0 0; cursor:pointer; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# ---------- Session ----------
def ss_get(key, default):
    if key not in st.session_state: st.session_state[key] = default
    return st.session_state[key]

messages: List[Dict[str, str]] = ss_get("messages", [])
mode: str = ss_get("mode", "VIA")                       # user chooses only VIA or DOMA
inventory_df: Optional[pd.DataFrame] = ss_get("inventory_df", None)
last_structured: Dict[str, Any] = ss_get("last_structured", {})
email_to: str = ss_get("email_to", "")
last_suggestions: Dict[str, Any] = ss_get("last_suggestions", {"key": "", "items": []})
pending_suggestion: str = ss_get("pending_suggestion", "")

# ---------- Header ----------
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;">
  <div style="width:40px;height:40px;border-radius:10px;background:#6c5ce7;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;">B</div>
  <div>
    <h2 style="margin:0;">BuildWise AI</h2>
    <p style="margin:0;opacity:.7;">VIA (new tenants) · DOMA (existing tenants) — auto-routed by Manager Agent</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 🧭 Workflow")
    mode = st.radio("Choose pipeline", options=["VIA", "DOMA"], index=0 if mode=="VIA" else 1, help="You pick VIA or DOMA; Manager routes to the right sub-agent.")
    st.session_state["mode"] = mode

    st.markdown("### 📂 Listings CSV")
    up = st.file_uploader("Upload inventory (id, address, neighborhood, sqft, rent, amenities)", type="csv")
    if up:
        try:
            inventory_df = pd.read_csv(up)
            st.session_state["inventory_df"] = inventory_df
            st.success(f"Loaded `{up.name}` ({len(inventory_df)} rows)")
            st.dataframe(inventory_df.head(8), use_container_width=True)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

    st.markdown("### ✉️ Send summary")
    email_to = st.text_input("Recipient email", value=email_to, placeholder="agent@brokerage.com")
    st.session_state["email_to"] = email_to

# ---------- Demo data ----------
DEFAULT_SLOTS = [
    {"start": "2025-08-12T15:30:00Z", "end": "2025-08-12T16:00:00Z"},
    {"start": "2025-08-13T14:00:00Z", "end": "2025-08-13T14:30:00Z"},
]

# =========================================================
# VIA agents
# =========================================================
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
    "Infer cautiously. Include a confidence 0..1 per field. "
    "If budget is implausibly low for the given area, set spec_status:'underconstrained' and suggest adjustments."
)

class NeedsAgent:
    def run(self, user_text: str, sample_rows: Optional[str]) -> SearchSpec:
        msgs = [{"role":"system","content":VIA_SYSTEM}]
        ctx = f"User says: {user_text}"
        if sample_rows: ctx += f"\nSample inventory rows:\n{sample_rows}"
        msgs.append({"role":"user","content":ctx})
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=msgs,
            response_format={"type":"json_object"}
        )
        return SearchSpec.model_validate_json(resp.choices[0].message.content)

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
    def __init__(self, rows: List[Dict[str, Any]]): self.rows = rows

    def _must_ok(self, row, spec):
        musts = {m.lower() for m in spec.get("must_haves", [])}
        amenities = row.get("amenities", [])
        if isinstance(amenities, str):
            try: amenities = json.loads(amenities)
            except: amenities = [amenities]
        amenities = {str(a).lower() for a in amenities}
        return musts.issubset(amenities) if musts else True

    def _score(self, row, spec):
        s = 0.0
        if spec.get("min_sqft") and row.get("sqft") and row["sqft"] >= spec["min_sqft"]: s += 20
        if spec.get("max_sqft") and row.get("sqft") and row["sqft"] <= spec["max_sqft"]: s += 20
        if spec.get("budget_monthly_usd") and row.get("rent") is not None:
            lo, hi = spec["budget_monthly_usd"].get("min"), spec["budget_monthly_usd"].get("max")
            if lo is not None and row["rent"] >= lo: s += 15
            if hi is not None and row["rent"] <= hi: s += 15
        if spec.get("location") and row.get("neighborhood"):
            if any(loc.lower() in str(row["neighborhood"]).lower() for loc in spec["location"]): s += 20
        return max(0.0, min(100.0, s))

    def run(self, spec: Dict[str, Any], topn=5) -> MatchResult:
        cands: List[MatchItem] = []
        for row in self.rows:
            if not self._must_ok(row, spec): continue
            sc = self._score(row, spec)
            reasons = []
            if row.get("neighborhood"): reasons.append(f"Neighborhood match: {row['neighborhood']}")
            if row.get("sqft"): reasons.append(f"{row['sqft']} sqft fits")
            if row.get("rent") is not None: reasons.append(f"Rent ${row['rent']} in range")
            cands.append(MatchItem(
                id=str(row.get("id", row.get("address",""))),
                score=sc,
                reasons=reasons[:3],
                row_preview=row
            ))
        cands.sort(key=lambda x: x.score, reverse=True)
        relaxed = None
        if len(cands) < 3 and spec.get("max_sqft"):
            spec["max_sqft"] = int(spec["max_sqft"] * 1.1)
            relaxed = "max_sqft"
            for c in cands: c.relaxed_field = relaxed
        return MatchResult(matches=cands[:topn], spec_used=spec)

class ActionPlan(BaseModel):
    actions: List[Dict[str, Any]]
    confirmation_prompt: str

class TourCloseAgent:
    def __init__(self, slots: List[Dict[str, str]]): self.slots = slots
    def run(self, matches: List[Dict[str, Any]]) -> ActionPlan:
        props = []
        for m in matches[:2]:
            slot = self.slots[0] if self.slots else {"start":"2025-08-12T15:30:00Z","end":"2025-08-12T16:00:00Z"}
            props.append({
                "type":"tour",
                "unit_id": m.get("id"),
                "address": m.get("row_preview",{}).get("address",""),
                "start": slot["start"], "end": slot["end"],
                "required_docs": ["photo_id","income_proof"]
            })
        return ActionPlan(actions=props, confirmation_prompt="Book tour 1, tour 2, or propose other times?")

class VIAAgent:
    def __init__(self, inventory_rows: List[Dict[str, Any]], slots: List[Dict[str, str]]):
        self.needs = NeedsAgent()
        self.matcher = MatchRankAgent(rows=inventory_rows)
        self.closer = TourCloseAgent(slots)
        self.inventory_rows = inventory_rows
        self.slots = slots

    def handle_full(self, user_text: str, sample_rows: Optional[str]) -> Dict[str, Any]:
        spec = self.needs.run(user_text, sample_rows)
        mres = self.matcher.run(spec=spec.model_dump())
        plan = self.closer.run([m.model_dump() for m in mres.matches])
        return {"stage":"VIA","search_spec":spec.model_dump(),
                "matches":[m.model_dump() for m in mres.matches],
                "action_plan":plan.model_dump()}

# =========================================================
# DOMA agents
# =========================================================
DOMA_SYSTEM = (
    "You answer strictly from retrieved lease text. Cite section or page. "
    "If not found, say 'Not found in provided lease' and suggest escalation."
)

class LeaseAnswer(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    risk_flags: List[str] = []

class LeaseQAAgent:
    def run(self, question: str, chunks: List[Dict[str, Any]]) -> LeaseAnswer:
        context = "\n\n".join([f"[{c.get('source','lease')} p{c.get('page','?')}] {c.get('text','')}" for c in chunks])
        msgs = [
            {"role":"system","content":DOMA_SYSTEM},
            {"role":"user","content":f"Lease snippets:\n{context}\n\nQuestion: {question}\nAnswer concisely with inline citations."}
        ]
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
        txt = resp.choices[0].message.content
        cits = [{"section":"unknown","page": c.get("page")} for c in chunks[:2]]
        return LeaseAnswer(answer=txt, citations=cits)

class TriageResult(BaseModel):
    category: str
    priority: str
    vendor: str
    eta_hours: int
    confirm_message: str

EMERGENCY = {"gas leak","water main break","sparks","smoke"}

class ServiceTriageAgent:
    def run(self, ticket_text: str) -> TriageResult:
        t = ticket_text.lower()
        if any(k in t for k in EMERGENCY):
            return TriageResult(
                category="emergency", priority="P0", vendor="dispatch_call_center", eta_hours=1,
                confirm_message="Emergency detected. Dispatching immediately. If unsafe, evacuate and call local emergency services."
            )
        category = "plumbing" if "leak" in t else "hvac" if ("ac" in t or "air" in t) else "general"
        vendor = "preferred_plumber_inc" if category=="plumbing" else "preferred_hvac_llc" if category=="hvac" else "handyman_pool"
        eta = 8 if category in ("plumbing","hvac") else 24
        return TriageResult(category=category, priority="P2", vendor=vendor, eta_hours=eta,
                            confirm_message=f"Ticket logged as {category}. Assigned {vendor}. ETA within {eta} hours.")

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
        primary = Offer(rent_usd=target, term_months=12, incentives=["touch-up paint"])
        alt1 = Offer(rent_usd=round(target*0.98,2), term_months=24, incentives=["1 month free end of term"])
        alt2 = Offer(rent_usd=round(target*1.01,2), term_months=12, incentives=["new appliance package"])
        approval = not (policy_floor <= primary.rent_usd <= policy_ceiling)
        just = f"Anchored to market median ${comps_median:,.0f}, within policy [{policy_floor:,.0f}–{policy_ceiling:,.0f}]."
        return RenewalPackage(primary=primary, alternatives=[alt1,alt2], justification=just, needs_manager_approval=approval)

# =========================================================
# Manager Agent — auto-routing inside VIA/DOMA
# =========================================================
class ManagerAgent:
    VIA_INTENTS = {
        "needs": ["need", "looking", "find", "search", "budget", "sqft", "move", "location"],
        "tour":  ["tour", "visit", "schedule", "see", "book"],
    }
    DOMA_INTENTS = {
        "lease":   ["lease", "renewal notice", "deposit", "fee", "clause", "term", "sublet"],
        "triage":  ["leak", "broken", "repair", "hvac", "ac", "heater", "issue", "maintenance", "gas", "smoke", "water"],
        "renewal": ["renew", "extend", "offer", "increase", "rent proposal", "counter"],
    }

    def via_route(self, text: str) -> str:
        t = text.lower()
        if any(k in t for k in self.VIA_INTENTS["tour"]):   return "tour"
        return "needs"

    def doma_route(self, text: str) -> str:
        t = text.lower()
        if any(k in t for k in self.DOMA_INTENTS["triage"]):  return "triage"
        if any(k in t for k in self.DOMA_INTENTS["renewal"]): return "renewal"
        return "lease"

    def handle_via(self, user_text: str, inventory: List[Dict[str,Any]], slots: List[Dict[str,str]], sample_rows: Optional[str]) -> Dict[str,Any]:
        route = self.via_route(user_text)
        via = VIAAgent(inventory_rows=inventory, slots=slots)
        return {"route":"VIA/"+route, **via.handle_full(user_text, sample_rows)}

    def handle_doma(self, user_text: str, pasted_lease: str) -> Dict[str,Any]:
        route = self.doma_route(user_text)
        if route == "triage":
            tri = ServiceTriageAgent().run(ticket_text=user_text)
            return {"route":"DOMA/triage", "triage": tri.model_dump()}
        elif route == "renewal":
            pkg = RenewalDealAgent().run(current_rent=3200, comps_median=3300, policy_floor=3000, policy_ceiling=3600)
            return {"route":"DOMA/renewal", "renewal": pkg.model_dump()}
        else:
            chunks=[]
            if pasted_lease.strip():
                for i, blk in enumerate(pasted_lease.split("\n\n")):
                    chunks.append({"source":"lease","page":i+1,"text":blk[:1200]})
            ans = LeaseQAAgent().run(question=user_text, chunks=chunks)
            return {"route":"DOMA/lease", "lease_answer": ans.model_dump()}

manager = ManagerAgent()

# =========================================================
# Prompt Helper — suggestions from chat history
# =========================================================
def generate_suggestions(history: List[Dict[str,str]], mode: str) -> List[str]:
    """
    Uses last 6 turns to propose 2–4 follow-up prompts.
    Falls back to heuristics if the API call fails.
    """
    if not history:
        return ["Find offices in Midtown under $4,500/mo", "What documents do I need to book a tour?"] if mode=="VIA" \
               else ["When is my renewal notice due?", "Log a maintenance ticket for a bathroom leak"]

    key = f"{mode}|{len(history)}|{history[-1]['content'][:80]}"
    if last_suggestions.get("key") == key:
        return last_suggestions.get("items", [])

    try:
        snippet = "\n".join([f"{m['role']}: {m['content']}" for m in history[-6:]])
        sys_prompt = (
            "You generate short follow-up prompts (max 12 words each), helpful and concrete, "
            f"for the '{mode}' workflow in a real-estate assistant. Return JSON list of strings only."
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":sys_prompt},
                      {"role":"user","content":f"Chat snippet:\n{snippet}\n\nPropose 3 helpful follow-ups."}],
            response_format={"type":"json_object"}
        )
        data = json.loads(resp.choices[0].message.content)
        items = data.get("suggestions") or data.get("items") or list(data.values())[0]
        items = [s.strip() for s in items if isinstance(s, str)][:4]
    except Exception:
        if mode == "VIA":
            items = ["Show top 3 options closer to subway",
                     "Can we tour this Tuesday at 3pm?",
                     "Relax max_sqft and re-run matches"]
        else:
            items = ["What is the late fee policy?",
                     "Create a service ticket: AC not cooling",
                     "Propose a 24-month renewal option"]

    st.session_state["last_suggestions"] = {"key": key, "items": items}
    return items

# =========================================================
# Helpers
# =========================================================
def ensure_welcome():
    if not messages:
        messages.append({"role":"assistant","content":"Hi! I’m BuildWise AI.\n\nSelect **VIA** or **DOMA** in the sidebar. I’ll auto-route your message to the right agent.\n- VIA: tell me area, budget, size, must-haves.\n- DOMA: ask about your lease, describe a maintenance issue, or request a renewal offer."})

def inventory_records() -> List[Dict[str, Any]]:
    if inventory_df is None or inventory_df.empty: return []
    df = inventory_df.copy()
    if "amenities" in df.columns:
        def to_list(v):
            if isinstance(v, list): return v
            try: return json.loads(v)
            except: return [str(v)] if pd.notna(v) else []
        df["amenities"] = df["amenities"].apply(to_list)
    return df.to_dict(orient="records")

def summarize_via(res: Dict[str, Any]) -> str:
    if not res or "matches" not in res: return "No results."
    ms = res["matches"]
    lines = []
    for m in ms[:3]:
        rp = m.get("row_preview", {})
        lines.append(f"• {rp.get('address','')} ({rp.get('neighborhood','')}) — {rp.get('sqft','?')} sqft, ${rp.get('rent','?')}/mo — score {int(m.get('score',0))}")
    plan = res.get("action_plan",{}).get("confirmation_prompt","")
    return f"**Top matches**\n" + "\n".join(lines) + ("\n\n" + plan if plan else "")

def build_email_summary(conv: List[Dict[str,str]], structured: Dict[str,Any]) -> str:
    lines = ["Subject: BuildWise AI — Conversation Summary","","Hello team","","Here is the latest BuildWise AI conversation summary.",""]
    for m in conv[-12:]:
        who = "User" if m["role"]=="user" else "Assistant"
        lines.append(f"{who}: {m['content']}")
    lines.append("")
    if structured.get("VIA"):
        lines.append("— VIA Result —")
        lines.append(json.dumps(structured["VIA"], indent=2))
    if structured.get("DOMA"):
        lines.append("— DOMA Result —")
        lines.append(json.dumps(structured["DOMA"], indent=2))
    lines.append("")
    lines.append("Best,")
    lines.append("BuildWise AI")
    return "\n".join(lines)

# =========================================================
# Layout
# =========================================================
col_chat, col_right = st.columns([0.58, 0.42])

# ---------------- LEFT: ChatGPT-like transcript ----------------
with col_chat:
    # header controls
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🧹 Clear chat", use_container_width=True):
            st.session_state["messages"] = []
            st.session_state["last_structured"] = {}
            st.session_state["last_suggestions"] = {"key":"", "items":[]}
            messages = []
            st.rerun()
    with c2:
        regenerate = st.button("🔁 Regenerate", use_container_width=True)

    # render full history
    ensure_welcome()
    for msg in messages:
        with st.chat_message(msg["role"], avatar=("🧑" if msg["role"]=="user" else "🤖")):
            st.markdown(msg["content"])

    # helper to run ManagerAgent and produce assistant_text + structured
    def run_manager_and_reply(user_text: str):
        if st.session_state["mode"] == "VIA":
            inv = inventory_records()
            sample = inventory_df.head(3).to_string() if (inventory_df is not None and not inventory_df.empty) else None
            with st.spinner("Manager → VIA (needs → match → tour)…"):
                res = manager.handle_via(user_text=user_text, inventory=inv, slots=DEFAULT_SLOTS, sample_rows=sample)
            st.session_state["last_structured"] = {"VIA": res}
            reply = f"_{res['route']}_\n\n" + summarize_via(res)
        else:
            pasted = st.session_state.get("lease_paste", "")
            with st.spinner("Manager → DOMA…"):
                res = manager.handle_doma(user_text=user_text, pasted_lease=pasted)
            st.session_state["last_structured"] = {"DOMA": res}
            if "lease_answer" in res:
                reply = f"_{res['route']}_\n\n**Lease answer**\n\n{res['lease_answer']['answer']}"
            elif "triage" in res:
                reply = f"_{res['route']}_\n\n**Service ticket**\n\n{res['triage']['confirm_message']}"
            else:
                p = res["renewal"]["primary"]
                reply = f"_{res['route']}_\n\n**Renewal offer**\n\n${p['rent_usd']:,.0f}/mo · {p['term_months']} mo · {', '.join(p['incentives'])}"
        return reply

    # regenerate last answer
    if regenerate and any(m["role"] == "user" for m in messages):
        last_user = [m for m in messages if m["role"] == "user"][-1]["content"]
        new_reply = run_manager_and_reply(last_user)
        messages.append({"role": "assistant", "content": new_reply})
        st.session_state["messages"] = messages
        st.rerun()

# ------- Prompt Helper: suggestions as clickable chips -------
suggest_items = generate_suggestions(messages, mode)
if suggest_items:
    st.caption("Suggestions")
    cols = st.columns(min(4, len(suggest_items)))
    clicked = None
    for i, s in enumerate(suggest_items):
        with cols[i % len(cols)]:
            if st.button(s, key=f"sugg_{i}", help="Use this suggestion"):
                clicked = s
    if clicked:
        # auto-send this suggestion as the next user message
        st.session_state["pending_suggestion"] = clicked
        st.rerun()

# ---------- Chat input ----------
default_placeholder = "Type here… I’ll auto-route inside VIA/DOMA"

# If a suggestion was clicked, send it immediately (without waiting for typing)
if st.session_state.get("pending_suggestion"):
    user_input = st.session_state["pending_suggestion"]
    st.session_state["pending_suggestion"] = ""
else:
    # ✅ Correct usage: only 'placeholder' + 'key'
    user_input = st.chat_input(placeholder=default_placeholder, key="chat_in")

if user_input:
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)
    messages.append({"role": "user", "content": user_input})

    assistant_text = run_manager_and_reply(user_input)
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(assistant_text)

    messages.append({"role": "assistant", "content": assistant_text})
    st.session_state["messages"] = messages

# ---------------- RIGHT: Results / tools ----------------
with col_right:
    if mode == "VIA":
        st.markdown("### 🔎 VIA — New Tenant")
        st.caption("Manager routes your request to Needs → Match → Tour")
        if inventory_df is None or inventory_df.empty:
            st.info("Upload a listings CSV in the sidebar for best VIA results.")
        if last_structured.get("VIA"):
            res = last_structured["VIA"]
            with st.container():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("#### Search spec")
                st.json(res.get("search_spec", {}))
                st.markdown("<hr class='soft'/>", unsafe_allow_html=True)
                st.markdown("#### Top matches")
                st.json(res.get("matches", [])[:3])
                st.markdown("<hr class='soft'/>", unsafe_allow_html=True)
                st.markdown("#### Action plan")
                st.json(res.get("action_plan", {}))
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("### 🛠️ DOMA — Existing Tenant")
        st.caption("Lease Q&A · Service Triage · Renewals (auto-routed)")
        with st.expander("📄 Paste lease clauses (for lease questions)"):
            st.text_area("Paste relevant text", height=160, key="lease_paste")
        if last_structured.get("DOMA"):
            dom = last_structured["DOMA"]
            if dom.get("lease_answer"):
                with st.container():
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.markdown("#### Lease Answer")
                    st.write(dom["lease_answer"].get("answer",""))
                    st.markdown("**Citations**")
                    st.json(dom["lease_answer"].get("citations", []))
                    st.markdown("</div>", unsafe_allow_html=True)
            if dom.get("triage"):
                with st.container():
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.markdown("#### Service Ticket")
                    st.json(dom["triage"])
                    st.markdown("</div>", unsafe_allow_html=True)
            if dom.get("renewal"):
                with st.container():
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.markdown("#### Renewal Package")
                    st.json(dom["renewal"])
                    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr class='soft'/>", unsafe_allow_html=True)
    st.markdown("#### ✉️ Share conversation")
    email_body = build_email_summary(messages, last_structured)
    st.download_button(
        label="Download email draft (.txt)",
        data=email_body.encode("utf-8"),
        file_name="buildwise_conversation_summary.txt",
        mime="text/plain"
    )
    if email_to.strip():
        st.caption(f"Ready to send to: **{email_to}** (use your mail client or wire SMTP later)")
    else:
        st.caption("Tip: add a recipient in the sidebar to show who will receive the summary.")

st.markdown("<hr class='soft'/>", unsafe_allow_html=True)
st.caption("🏢 BuildWise AI — Manager Agent + Prompt Helper • Chat history aware • Upload data in the sidebar")
