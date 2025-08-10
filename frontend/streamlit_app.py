# frontend/streamlit_app.py
import os, sys, json, math, datetime as dt
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import streamlit as st
from pydantic import BaseModel, Field
from openai import OpenAI

# allow local imports later if you split files
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
.block-container { padding-top: 1.0rem; padding-bottom: 1.0rem; }
.card { border:1px solid #e5e7eb; background:#fff; border-radius:14px; padding:16px; margin-bottom:12px;}
.badge {display:inline-block; padding:2px 8px; border-radius:999px; border:1px solid #e5e7ff; background:#eef2ff; font-size:12px; margin-right:6px;}
hr.soft { border:none; border-top:1px solid #eee; margin:12px 0; }
.suggestion-chip { display:inline-block; padding:6px 10px; border-radius:999px; border:1px solid #e0e7ff; background:#eef2ff; margin:4px 6px 0 0; cursor:pointer; font-size:13px; }
.small {font-size:12px; opacity:.8}
</style>
""", unsafe_allow_html=True)

# ---------- Session ----------
def ss_get(key, default):
    if key not in st.session_state: st.session_state[key] = default
    return st.session_state[key]

messages: List[Dict[str, str]] = ss_get("messages", [])
mode: str = ss_get("mode", "VIA")
inventory_df: Optional[pd.DataFrame] = ss_get("inventory_df", None)
last_structured: Dict[str, Any] = ss_get("last_structured", {})
email_to: str = ss_get("email_to", "")
lead_name: str = ss_get("lead_name", "")
lead_email: str = ss_get("lead_email", "")
last_suggestions: Dict[str, Any] = ss_get("last_suggestions", {"key": "", "items": []})
pending_suggestion: str = ss_get("pending_suggestion", "")
holds: List[Dict[str,Any]] = ss_get("holds", [])

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
    mode = st.radio("Choose pipeline", options=["VIA", "DOMA"], index=0 if mode=="VIA" else 1)
    st.session_state["mode"] = mode

    st.markdown("### 👤 Lead")
    lead_name = st.text_input("Full name", value=lead_name, placeholder="Jane Doe")
    lead_email = st.text_input("Email", value=lead_email, placeholder="jane@email.com")
    st.session_state["lead_name"] = lead_name
    st.session_state["lead_email"] = lead_email

    st.markdown("### 📂 Listings CSV")
    up = st.file_uploader("Upload inventory (id, address, neighborhood, sqft, rent, amenities, transit, pets)", type="csv")
    if up:
        try:
            raw_df = pd.read_csv(up)
            def normalize_inventory_df(df: pd.DataFrame) -> pd.DataFrame:
                colmap = {
                    "Property Address":"address","Address":"address",
                    "Neighborhood":"neighborhood","Area":"neighborhood","Borough":"neighborhood",
                    "Monthly Rent":"rent","Rent":"rent","Price":"rent","Asking Rent":"rent",
                    "Square Feet":"sqft","SQFT":"sqft","Size (SF)":"sqft","Size":"sqft",
                    "unique_id":"id","ID":"id","Unit ID":"id",
                    "Amenities":"amenities","Amenity":"amenities",
                    "Transit":"transit","Near Transit":"transit",
                    "Pets":"pets","Pet Friendly":"pets",
                    "Floor":"floor","Suite":"suite","Unit":"suite",
                    "Rent/SF/Year":"ppsf_year","$PSF/Yr":"ppsf_year","$/SF/Yr":"ppsf_year",
                    "Annual Rent":"annual_rent"
                }
                df = df.rename(columns={k:v for k,v in colmap.items() if k in df.columns})

                def _num(x):
                    if pd.isna(x): return None
                    if isinstance(x,(int,float)): return float(x)
                    s = str(x).lower().replace("$","").replace(",","").replace("sqft","").replace("/sf/yr","").replace("/sf/year","").strip()
                    try: return float(s)
                    except: return None

                # numbers
                for c in ("rent","sqft","ppsf_year"):
                    if c in df.columns: df[c] = df[c].apply(_num)
                if "annual_rent" in df.columns: df["annual_rent"] = df["annual_rent"].apply(_num)

                # fill derived: if only ppsf_year + sqft -> rent; if only annual_rent -> rent
                if "rent" not in df.columns: df["rent"] = None
                if "sqft" not in df.columns: df["sqft"] = None
                if "ppsf_year" in df.columns:
                    df.loc[df["rent"].isna() & df["ppsf_year"].notna() & df["sqft"].notna(),
                           "rent"] = (df["ppsf_year"] * df["sqft"] / 12.0).round(0)
                if "annual_rent" in df.columns:
                    df.loc[df["rent"].isna() & df["annual_rent"].notna(), "rent"] = (df["annual_rent"]/12.0).round(0)

                # amenities -> list
                if "amenities" in df.columns:
                    def _to_list(v):
                        if isinstance(v, list): return v
                        if pd.isna(v): return []
                        try: return json.loads(v)
                        except: return [a.strip() for a in str(v).replace(";",",").split(",") if a.strip()]
                    df["amenities"] = df["amenities"].apply(_to_list)
                else:
                    df["amenities"] = [[] for _ in range(len(df))]

                # transit + pets flags
                def _to_bool(x): 
                    s = str(x).lower()
                    return any(k in s for k in ["yes","true","1","pet","allowed","friendly"])
                df["pet_friendly"] = df.get("pets", pd.Series([""]*len(df))).apply(_to_bool)
                df["near_transit"] = df.get("transit", pd.Series([""]*len(df))).astype(str).str.len().gt(0)

                # ids/addresses
                if "id" not in df.columns: df["id"] = df.index.astype(str)
                if "address" not in df.columns: df["address"] = ""
                if "neighborhood" not in df.columns: df["neighborhood"] = ""

                return df

            inventory_df = normalize_inventory_df(raw_df)
            st.session_state["inventory_df"] = inventory_df
            st.success(f"Loaded `{up.name}` ({len(inventory_df)} rows)")
            st.dataframe(inventory_df.head(10), use_container_width=True)
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
    "You are a real-estate intake specialist with a warm, concise voice. "
    "Output ONLY valid JSON for 'SearchSpec'. If the request lacks budget and size, set spec_status:'underconstrained'. "
    "Never invent numbers; include confidence per field."
)
TONE_SYSTEM = (
    "You are BuildWise, a friendly real-estate assistant. "
    "Write natural, upbeat replies (80–140 words) and end with ONE clear next step."
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
        raw = resp.choices[0].message.content

        def _coerce(d: dict) -> dict:
            d = dict(d or {})
            if isinstance(d.get("location"), str): d["location"] = [d["location"]]
            if not isinstance(d.get("location"), list): d["location"] = []
            b = d.get("budget_monthly_usd")
            if isinstance(b,(int,float,str)):
                try: d["budget_monthly_usd"] = {"min":None,"max": float(str(b).replace(",","").replace("$",""))}
                except: d["budget_monthly_usd"] = None
            elif isinstance(b, dict):
                m={}
                for k in ("min","max"):
                    v=b.get(k)
                    try: m[k]=None if v in (None,"",[]) else float(str(v).replace(",","").replace("$",""))
                    except: m[k]=None
                d["budget_monthly_usd"]=m
            else:
                d["budget_monthly_usd"]=None
            for k in ("must_haves","nice_to_haves"):
                v=d.get(k); 
                if isinstance(v,str): d[k]=[v]
                elif not isinstance(v,list): d[k]=[]
            for k in ("min_sqft","max_sqft","term_months"):
                if d.get(k) is not None:
                    try: d[k]=int(float(d[k])); 
                    except: d[k]=None
            if not isinstance(d.get("confidence"), dict): d["confidence"]={}
            if d.get("spec_status") not in ("ok","underconstrained"): d["spec_status"]="ok"
            return d

        try:
            data = json.loads(raw)
            return SearchSpec(**_coerce(data))
        except Exception:
            return SearchSpec(spec_status="underconstrained")

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

def _score_row(row: Dict[str,Any], spec: Dict[str,Any]) -> Tuple[float,List[str]]:
    s = 0.0; reasons=[]
    # size fit
    sqft = row.get("sqft")
    if spec.get("min_sqft") and sqft and sqft >= spec["min_sqft"]:
        s += 18; reasons.append(f"{int(sqft)} SF fits")
    if spec.get("max_sqft") and sqft and sqft <= spec["max_sqft"]:
        s += 12
    # price fit
    rent = row.get("rent")
    if spec.get("budget_monthly_usd") and rent is not None:
        lo, hi = spec["budget_monthly_usd"].get("min"), spec["budget_monthly_usd"].get("max")
        if hi is not None and rent <= hi: s += 22; reasons.append(f"Rent {_fmt_money(rent)} within budget")
        elif hi is not None: reasons.append(f"Rent {_fmt_money(rent)} above budget")
        if lo is not None and rent >= lo: s += 6
    # location
    if spec.get("location"):
        text = " ".join([str(row.get(k,"")) for k in ("neighborhood","address")])
        if any(loc.lower() in text.lower() for loc in spec["location"]):
            s += 16; reasons.append("Neighborhood match")
    # must-haves (amenities)
    musts = {m.lower() for m in spec.get("must_haves", [])}
    am = row.get("amenities", [])
    am = {str(a).lower() for a in (am if isinstance(am, list) else [am])}
    if musts:
        have = musts.intersection(am)
        s += 10 * (len(have)/max(1,len(musts)))
        if have: reasons.append("Has: " + ", ".join(sorted(list(have))[:3]))
    # transit / pets
    if row.get("near_transit"): s += 8; reasons.append("Close to transit")
    if row.get("pet_friendly") and ("pet" in " ".join(musts) or "dog" in " ".join(musts)): s += 8; reasons.append("Pet-friendly")
    return max(0.0, min(100.0, s)), reasons[:3]

class MatchRankAgent:
    def __init__(self, rows: List[Dict[str, Any]]): self.rows = rows
    def run(self, spec: Dict[str, Any], topn=5) -> MatchResult:
        cands: List[MatchItem] = []
        for row in self.rows:
            sc, reasons = _score_row(row, spec)
            cands.append(MatchItem(
                id=str(row.get("id", row.get("address",""))),
                score=sc, reasons=reasons, row_preview=row
            ))
        cands.sort(key=lambda x: x.score, reverse=True)
        # even if all scores low, return top N with reason codes (soft fail)
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
    def handle_full(self, user_text: str, sample_rows: Optional[str]) -> Dict[str, Any]:
        spec = self.needs.run(user_text, sample_rows)
        mres = self.matcher.run(spec=spec.model_dump())
        plan = self.closer.run([m.model_dump() for m in mres.matches])
        return {"stage":"VIA","search_spec":spec.model_dump(),
                "matches":[m.model_dump() for m in mres.matches],
                "action_plan":plan.model_dump()}

# =========================================================
# DOMA agents (same as before, shortened for brevity)
# =========================================================
DOMA_SYSTEM = ("Answer only from lease text; cite page/section; if unknown, say so.")
class LeaseAnswer(BaseModel): answer: str; citations: List[Dict[str,Any]]; risk_flags: List[str]=[]
class LeaseQAAgent:
    def run(self, question: str, chunks: List[Dict[str, Any]]) -> LeaseAnswer:
        ctx = "\n\n".join([f"[p{c.get('page','?')}] {c.get('text','')}" for c in chunks])
        msgs=[{"role":"system","content":DOMA_SYSTEM},
              {"role":"user","content":f"Lease snippets:\n{ctx}\n\nQ: {question}\nReply concisely with inline citations."}]
        r = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
        return LeaseAnswer(answer=r.choices[0].message.content, citations=[{"page":c.get("page")} for c in chunks[:2]])

class TriageResult(BaseModel):
    category:str; priority:str; vendor:str; eta_hours:int; confirm_message:str
class ServiceTriageAgent:
    def run(self, ticket_text: str) -> TriageResult:
        t=ticket_text.lower()
        if any(k in t for k in ["gas","smoke","water main"]):
            return TriageResult("emergency","P0","dispatch_call_center",1,"Emergency detected. Dispatching now.")
        cat="plumbing" if "leak" in t else "hvac" if ("ac" in t or "air" in t) else "general"
        vendor={"plumbing":"preferred_plumber_inc","hvac":"preferred_hvac_llc"}.get(cat,"handyman_pool")
        return TriageResult(cat,"P2",vendor,8 if cat!="general" else 24,f"Ticket logged as {cat}. Assigned {vendor}.")

class Offer(BaseModel): rent_usd:float; term_months:int; incentives:List[str]=[]
class RenewalPackage(BaseModel):
    primary:Offer; alternatives:List[Offer]; justification:str; needs_manager_approval:bool=False
class RenewalDealAgent:
    def run(self, current_rent: float, comps_median: float, policy_floor: float, policy_ceiling: float) -> RenewalPackage:
        tgt=max(policy_floor, min(comps_median, policy_ceiling))
        p=Offer(rent_usd=tgt, term_months=12, incentives=["touch-up paint"])
        a1=Offer(rent_usd=round(tgt*0.98,2), term_months=24, incentives=["1 month free"])
        a2=Offer(rent_usd=round(tgt*1.01,2), term_months=12, incentives=["new appliances"])
        return RenewalPackage(primary=p, alternatives=[a1,a2], justification="Anchored to market median.", needs_manager_approval=False)

# =========================================================
# Manager Agent
# =========================================================
class ManagerAgent:
    VIA_INTENTS={"needs":["need","looking","find","search","budget","sqft","move","location","house","apartment","office"],
                 "tour":["tour","visit","schedule","see","book"]}
    DOMA_INTENTS={"lease":["lease","deposit","fee","clause","term","sublet"],
                  "triage":["leak","broken","repair","hvac","ac","heater","issue","maintenance","gas","smoke","water"],
                  "renewal":["renew","extend","offer","increase","rent proposal","counter"]}
    def via_route(self, text:str)->str:
        t=text.lower()
        return "tour" if any(k in t for k in self.VIA_INTENTS["tour"]) else "needs"
    def doma_route(self, text:str)->str:
        t=text.lower()
        if any(k in t for k in self.DOMA_INTENTS["triage"]): return "triage"
        if any(k in t for k in self.DOMA_INTENTS["renewal"]): return "renewal"
        return "lease"
    def handle_via(self, user_text:str, inventory:List[Dict[str,Any]], slots:List[Dict[str,str]], sample_rows:Optional[str])->Dict[str,Any]:
        via=VIAAgent(inventory_rows=inventory, slots=slots)
        return {"route":"VIA/"+self.via_route(user_text), **via.handle_full(user_text, sample_rows)}
    def handle_doma(self, user_text:str, pasted_lease:str)->Dict[str,Any]:
        r=self.doma_route(user_text)
        if r=="triage": return {"route":"DOMA/triage", "triage": ServiceTriageAgent().run(user_text).model_dump()}
        if r=="renewal": return {"route":"DOMA/renewal", "renewal": RenewalDealAgent().run(3200,3300,3000,3600).model_dump()}
        chunks=[]
        if pasted_lease.strip():
            for i,blk in enumerate(pasted_lease.split("\n\n")): chunks.append({"page":i+1,"text":blk[:1200]})
        ans=LeaseQAAgent().run(user_text, chunks)
        return {"route":"DOMA/lease", "lease_answer": ans.model_dump()}

manager = ManagerAgent()

# =========================================================
# Friendly replies
# =========================================================
def _fmt_money(x):
    if x is None: return "—"
    try: return f"${int(round(float(x))):,}"
    except: return "—"

def _ppsf_year_calc(row):
    if isinstance(row.get("ppsf_year"), (int,float)): return round(float(row["ppsf_year"]),2)
    rent=row.get("rent"); sqft=row.get("sqft")
    try:
        if rent and sqft: return round((float(rent)*12)/float(sqft),2)
    except: pass
    return None

TONE_SYSTEM = (
    "You are BuildWise, a friendly, concise real-estate assistant. "
    "Summarize options in natural language (not JSON), keep 80–140 words, end with ONE clear next step."
)

def friendly_via_reply(res: Dict[str,Any], user_text: str) -> str:
    try:
        msgs=[{"role":"system","content":TONE_SYSTEM},
              {"role":"user","content":f"User query: {user_text}\nSearch spec: {json.dumps(res.get('search_spec',{}))}\nTop matches: {json.dumps(res.get('matches',[])[:3])}\nWrite a warm, helpful reply. If no matches, propose 2 specific adjustments."}]
        r=client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
        return r.choices[0].message.content
    except Exception:
        ms=res.get("matches",[])
        if not ms:
            return "I didn’t find a perfect fit yet. We can raise the budget slightly or open nearby neighborhoods. Should I try either?"
        lines=[]
        for m in ms[:3]:
            rp=m.get("row_preview",{})
            lines.append(f"- {rp.get('address','(pending)')} — {int(rp.get('sqft',0)) or '—'} SF · {_fmt_money(rp.get('rent'))}/mo")
        return "Here are a few that look promising:\n"+"\n".join(lines)+"\n\nWant me to book a tour for one of these?"

def friendly_lease_reply(ans: Dict[str,Any]) -> str:
    a = ans.get("lease_answer",{}).get("answer","")
    return f"Here’s what your lease says:\n\n{a}\n\nWant me to draft a quick note to your building manager or check renewal timelines?"

# ---------- VIA UI helpers ----------
def _slot_labels(slots):
    lbls=[]
    for s in slots:
        try:
            start=dt.datetime.fromisoformat(s["start"].replace("Z","+00:00"))
            lbls.append(start.strftime("%a %b %d · %I:%M %p"))
        except: lbls.append(s["start"])
    return lbls

def _row_friendly(row: Dict[str,Any]):
    return {
        "id": str(row.get("id","")),
        "address": row.get("address",""),
        "neighborhood": row.get("neighborhood",""),
        "sqft": row.get("sqft"),
        "rent_mo": row.get("rent"),
        "ppsf_year": _ppsf_year_calc(row),
        "floor": row.get("floor"),
        "suite": row.get("suite"),
        "near_transit": bool(row.get("near_transit", False)),
        "pet_friendly": bool(row.get("pet_friendly", False)),
        "amenities": row.get("amenities", [])
    }

# =========================================================
# Prompt Helper
# =========================================================
def generate_suggestions(history: List[Dict[str,str]], mode: str) -> List[str]:
    if not history:
        return ["Find places in Midtown under $4,500/mo","What docs do I need to book a tour?"] if mode=="VIA" \
               else ["When is my renewal notice due?","Create a maintenance ticket for a bathroom leak"]
    key=f"{mode}|{len(history)}|{history[-1]['content'][:80]}"
    if last_suggestions.get("key")==key: return last_suggestions["items"]
    try:
        snippet="\n".join([f"{m['role']}: {m['content']}" for m in history[-6:]])
        sys_prompt=("Return JSON {'suggestions':[...]} of 3 short, friendly, concrete follow-ups (<= 12 words) for "
                    f"{mode}.")
        r=client.chat.completions.create(model="gpt-4o-mini",
            messages=[{"role":"system","content":sys_prompt},{"role":"user","content":snippet}],
            response_format={"type":"json_object"})
        items=[s.strip() for s in json.loads(r.choices[0].message.content).get("suggestions",[]) if isinstance(s,str)][:4]
    except Exception:
        items=["Show top 3 near subway","Book a tour for Tue 3pm"] if mode=="VIA" else ["What’s the late fee policy?","Offer a 24-month option"]
    st.session_state["last_suggestions"]={"key":key,"items":items}; return items

# =========================================================
# Helpers
# =========================================================
def ensure_welcome():
    if not messages:
        hello = "Hi! I’m BuildWise. Tell me what you’re looking for and I’ll help. Choose **VIA** for new-place search, or **DOMA** for lease/maintenance/renewals."
        if lead_name: hello = f"Hi {lead_name}! " + hello
        messages.append({"role":"assistant","content":hello})

def inventory_records() -> List[Dict[str, Any]]:
    if inventory_df is None or inventory_df.empty: return []
    return inventory_df.to_dict(orient="records")

def build_email_summary(conv: List[Dict[str,str]], structured: Dict[str,Any]) -> str:
    lines=["Subject: BuildWise AI — Conversation Summary","","Hello team","","Here is the latest BuildWise AI conversation summary.",""]
    if lead_name or lead_email:
        lines += [f"Lead: {lead_name or '—'} · {lead_email or '—'}",""]
    for m in conv[-12:]:
        who="User" if m["role"]=="user" else "Assistant"; lines.append(f"{who}: {m['content']}")
    lines.append("")
    if structured.get("VIA"): lines.append("— VIA Result —\n"+json.dumps(structured["VIA"], indent=2))
    if structured.get("DOMA"): lines.append("— DOMA Result —\n"+json.dumps(structured["DOMA"], indent=2))
    lines += ["","Best,","BuildWise AI"]; return "\n".join(lines)

# =========================================================
# Layout
# =========================================================
col_chat, col_right = st.columns([0.58, 0.42])

# ---------------- LEFT: Chat transcript ----------------
with col_chat:
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("🧹 Clear chat", use_container_width=True):
            st.session_state["messages"]=[]
            st.session_state["last_structured"]={}
            st.session_state["last_suggestions"]={"key":"", "items":[]}
            st.session_state["holds"]=[]
            st.rerun()
    with c2:
        regenerate = st.button("🔁 Regenerate", use_container_width=True)

    ensure_welcome()
    for msg in messages:
        with st.chat_message(msg["role"], avatar=("🧑" if msg["role"]=="user" else "🤖")):
            st.markdown(msg["content"])

    def run_manager_and_reply(user_text: str):
        if st.session_state["mode"] == "VIA":
            inv = inventory_records()
            sample = inventory_df.head(3).to_string() if (inventory_df is not None and not inventory_df.empty) else None
            with st.spinner("Finding options for you…"):
                res = manager.handle_via(user_text=user_text, inventory=inv, slots=DEFAULT_SLOTS, sample_rows=sample)
            st.session_state["last_structured"] = {"VIA": res}
            msg = friendly_via_reply(res, user_text)
            if st.session_state.get("holds"):
                h = st.session_state["holds"][-1]; 
                msg += f"\n\nI put a temporary hold on **{h['address']}**. Shall I confirm the booking?"
            return f"_{res['route']}_\n\n" + msg
        else:
            pasted = st.session_state.get("lease_paste","")
            with st.spinner("Checking your lease/policy…"):
                res = manager.handle_doma(user_text=user_text, pasted_lease=pasted)
            st.session_state["last_structured"] = {"DOMA": res}
            if "lease_answer" in res: return f"_{res['route']}_\n\n" + friendly_lease_reply(res)
            if "triage" in res: return f"_{res['route']}_\n\n**Service ticket**\n\n{res['triage']['confirm_message']}\n\nShould I notify your vendor now?"
            p = res["renewal"]["primary"]
            return f"_{res['route']}_\n\nI can offer **${p['rent_usd']:,.0f}/mo for {p['term_months']} months** ({', '.join(p['incentives'])}).\n\nSend for approval or see alternatives?"

    if regenerate and any(m["role"] == "user" for m in messages):
        last_user = [m for m in messages if m["role"] == "user"][-1]["content"]
        messages.append({"role":"assistant","content":run_manager_and_reply(last_user)})
        st.session_state["messages"]=messages; st.rerun()

    # suggestions
    suggest_items = generate_suggestions(messages, mode)
    if suggest_items:
        st.caption("Suggestions")
        cols = st.columns(min(4, len(suggest_items)))
        clicked=None
        for i,s in enumerate(suggest_items):
            with cols[i%len(cols)]:
                if st.button(s, key=f"sugg_{i}"): clicked=s
        if clicked:
            st.session_state["pending_suggestion"]=clicked; st.rerun()

    placeholder = "Type here… I’ll auto-route inside VIA/DOMA"
    if st.session_state.get("pending_suggestion"):
        user_input = st.session_state["pending_suggestion"]; st.session_state["pending_suggestion"]=""
    else:
        user_input = st.chat_input(placeholder=placeholder, key="chat_in")

    if user_input:
        with st.chat_message("user", avatar="🧑"): st.markdown(user_input)
        messages.append({"role":"user","content":user_input})
        reply = run_manager_and_reply(user_input)
        with st.chat_message("assistant", avatar="🤖"): st.markdown(reply)
        messages.append({"role":"assistant","content":reply})
        st.session_state["messages"]=messages

# ---------------- RIGHT: Results / tools ----------------
with col_right:
    if mode == "VIA":
        st.markdown("### 🔎 VIA — New Tenant")
        st.caption("Manager routes your request to Needs → Match → Tour")

        if inventory_df is None or inventory_df.empty:
            st.info("Upload a listings CSV in the sidebar for best VIA results.")
        elif last_structured.get("VIA"):
            res = last_structured["VIA"]
            matches = res.get("matches", [])[:3]

            with st.expander("Search spec", expanded=False):
                st.json(res.get("search_spec", {}))

            st.markdown("#### Top matches")
            if not matches:
                st.warning("No perfect matches yet. Try adding a budget, sqft range, or a neighborhood.")
            else:
                for i,m in enumerate(matches, start=1):
                    rp=m.get("row_preview",{})
                    f=_row_friendly(rp)
                    with st.container():
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown(f"**{f['address']}**  ·  {f.get('neighborhood','')}")
                        colA,colB,colC,colD=st.columns([1,1,1,1])
                        with colA: st.metric("Rent / mo", _fmt_money(f["rent_mo"]))
                        with colB: st.metric("Size (SF)", f["sqft"] if f["sqft"] else "—")
                        with colC: st.metric("$ / SF / yr", f["ppsf_year"] if f["ppsf_year"] else "—")
                        with colD: st.write(f"*Floor:* {f['floor'] or '—'} · *Suite:* {f['suite'] or '—'}")

                        tags=[]
                        if f["near_transit"]: tags.append("Near transit")
                        if f["pet_friendly"]: tags.append("Pet-friendly")
                        if tags: st.markdown(" ".join([f"<span class='badge'>{t}</span>" for t in tags]), unsafe_allow_html=True)

                        # availability holds
                        st.markdown("**Visiting availability**")
                        labels=_slot_labels(DEFAULT_SLOTS)
                        cols=st.columns(len(labels))
                        for j,lbl in enumerate(labels):
                            with cols[j]:
                                if st.button(f"Hold {lbl}", key=f"hold_{f['id']}_{j}"):
                                    holds.append({"unit_id": f["id"], "address": f["address"], "slot": DEFAULT_SLOTS[j]})
                                    st.session_state["holds"]=holds
                                    st.success(f"Held {f['address']} · {lbl}")

                        if m.get("reasons"):
                            st.caption("Why it matches: " + " · ".join(m["reasons"]))
                        st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("#### Action plan")
            st.json(res.get("action_plan", {}))

            if matches:
                with st.expander("Compare options", expanded=False):
                    rows=[]
                    for m in matches:
                        r=m.get("row_preview",{}); fr=_row_friendly(r)
                        rows.append({
                            "Address": fr["address"],
                            "Neighborhood": fr.get("neighborhood",""),
                            "Rent/mo": _fmt_money(fr["rent_mo"]),
                            "Size (SF)": fr["sqft"] or "—",
                            "$/SF/yr": fr["ppsf_year"] or "—",
                            "Floor/Suite": f"{fr['floor'] or '—'}/{fr['suite'] or '—'}",
                            "Transit": "Yes" if fr["near_transit"] else "—",
                            "Pet-friendly": "Yes" if fr["pet_friendly"] else "—",
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True)

            # Quick refine chips
            st.markdown("#### Quick refine")
            c1,c2,c3=st.columns(3)
            if c1.button("↑ Budget +10%"): st.session_state["pending_suggestion"]="Raise budget by 10% and rerun matches"; st.rerun()
            if c2.button("↔ Expand area"): st.session_state["pending_suggestion"]="Include nearby neighborhoods and rerun matches"; st.rerun()
            if c3.button("↘ Relax sqft"): st.session_state["pending_suggestion"]="Relax max_sqft by 10% and rerun matches"; st.rerun()

    else:
        st.markdown("### 🛠️ DOMA — Existing Tenant")
        st.caption("Lease Q&A · Service Triage · Renewals (auto-routed)")
        with st.expander("📄 Paste lease clauses (for lease questions)"):
            st.text_area("Paste relevant text", height=160, key="lease_paste")
        if last_structured.get("DOMA"):
            dom=last_structured["DOMA"]
            if dom.get("lease_answer"):
                with st.container():
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.markdown("#### Lease Answer"); st.write(dom["lease_answer"].get("answer",""))
                    st.markdown("**Citations**"); st.json(dom["lease_answer"].get("citations", []))
                    st.markdown("</div>", unsafe_allow_html=True)
            if dom.get("triage"):
                with st.container():
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.markdown("#### Service Ticket"); st.json(dom["triage"]); st.markdown("</div>", unsafe_allow_html=True)
            if dom.get("renewal"):
                with st.container():
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.markdown("#### Renewal Package"); st.json(dom["renewal"]); st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr class='soft'/>", unsafe_allow_html=True)
    st.markdown("#### ✉️ Share conversation")
    email_body = build_email_summary(messages, last_structured)
    st.download_button("Download email draft (.txt)", email_body.encode("utf-8"),
                       file_name="buildwise_conversation_summary.txt", mime="text/plain")
    if email_to.strip(): st.caption(f"Ready to send to: **{email_to}**")
    else: st.caption("Tip: add a recipient in the sidebar.")

st.markdown("<hr class='soft'/>", unsafe_allow_html=True)
st.caption("🏢 BuildWise AI — Friendly tone • Weighted ranking • Visit holds • Quick refine • VIA/DOMA manager routing")
