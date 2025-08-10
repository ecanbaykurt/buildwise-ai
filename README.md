Got it — so instead of a business pitch, you want this section to be **research-heavy and technically deep**, showing your multi-agent architecture, design decisions, and future exploration areas, without touching pricing or revenue models.

Here’s the **research-focused README section** you can use for your open-source release.

---

# BuildWise AI — Research and Technical Architecture

## 1. Research Objective

BuildWise AI is an experimental, open-source framework for applying **multi-agent systems** to property leasing, tenant support, and portfolio analysis.
Its design is rooted in **natural language understanding**, **structured data ranking**, and **action-oriented AI outputs**, targeting real-world constraints in real estate operations.

---

## 2. Problem Space

In the property lifecycle, two key user types dominate interactions:

1. **Prospective tenants** — require fast, context-aware property matching and scheduling.
2. **Current tenants** — require accurate document Q\&A, service request triage, and renewal negotiation.

Traditional chatbots struggle with:

* Normalizing messy, incomplete user inputs into structured queries.
* Reasoning over heterogeneous datasets (buildings, units, leases, service tickets).
* Delivering **actionable next steps** rather than open-ended responses.

---

## 3. Multi-Agentic Structure

### High-Level Architecture

```
User
 └─▶ ManagerAgent
      ├─ VIA (Visit & Acquire — prospective tenants)
      │    ├─ NeedsAgent       → Extracts structured SearchSpec
      │    ├─ MatchRankAgent   → Ranks units against the SearchSpec
      │    └─ TourCloseAgent   → Generates actionable booking steps
      │
      └─ DOMA (Documents & Manage — current tenants)
           ├─ LeaseQAAgent     → Grounded Q&A from lease documents
           ├─ ServiceTriageAgent → Classifies and routes maintenance requests
           └─ RenewalDealAgent → Generates structured renewal offers
```

---

### Key Agent Pipelines

#### VIA — Prospective Tenant Workflow

1. **NeedsAgent**

   * Input: Free-text search query (e.g., “Looking for 2 bed, 1500 sqft near downtown”)
   * Output: `SearchSpec` (structured JSON with location\[], min/max sqft, budget, must-haves, timeline)
   * Method: LLM-based entity extraction + minimal clarifying questions if under-specified.

2. **MatchRankAgent**

   * Input: SearchSpec + unit dataset
   * Output: Ranked property list with scoring rationale.
   * Method: Rule-based scoring (size, price, location match, amenities) + deterministic sorting.

3. **TourCloseAgent**

   * Input: Top matches
   * Output: ActionPlan with 2–3 proposed viewing slots, confirmation prompt.
   * Method: Prompt-driven LLM formatting.

---

#### DOMA — Current Tenant Workflow

1. **LeaseQAAgent**

   * Input: Lease text (pasted or uploaded) + question
   * Output: Concise, citation-anchored answer.
   * Method: Context-limited retrieval from lease sections.

2. **ServiceTriageAgent**

   * Input: Free-text maintenance request
   * Output: `{category, urgency, recommended vendor, ETA}`
   * Method: Classification model + static vendor mapping.

3. **RenewalDealAgent**

   * Input: Tenant request + policy parameters + market comps
   * Output: RenewalPackage with primary and alternative offers.
   * Method: Heuristic rules + LLM text generation for justification.

---

## 4. Data Design

The system normalizes all inputs into **well-defined intermediate objects**:

| Structure        | Purpose                              |
| ---------------- | ------------------------------------ |
| `SearchSpec`     | Structured tenant search criteria    |
| `MatchItem`      | Property listing + score + reasoning |
| `ActionPlan`     | Next-step actions (e.g., book tour)  |
| `LeaseAnswer`    | Q\&A response with citation          |
| `TriageResult`   | Maintenance classification + routing |
| `RenewalPackage` | Structured offer set + justification |

---

## 5. Model Layer

* **LLM for NLU and reasoning:** Currently `gpt-4o-mini` for SearchSpec extraction, doc Q\&A, and renewal text.
* **Deterministic scoring for ranking:** Python-based rule weights for stability and reproducibility.
* **Retrieval:** Lease documents handled in-session; no external DB required for open-source build.
* **Optional extension:** Swap LLM endpoints, add vector DB (FAISS, Weaviate) for scalable document handling.

---

## 6. Interaction Flow Example (VIA)

1. User: “Looking for a 3-bedroom under \$3,500 in Brooklyn near transit”
2. **NeedsAgent** → Extract structured SearchSpec
3. **MatchRankAgent** → Score and rank available units
4. **TourCloseAgent** → Present top 3 units with proposed times and a “Book Tour” action

---

## 7. Interaction Flow Example (DOMA)

1. User: “What’s my sublet policy?” + paste lease
2. **LeaseQAAgent** → Return summary with section references
3. Alternative path: “Bathroom leak” → **ServiceTriageAgent** → Categorize, assign vendor, set ETA.

---

## 8. Research Goals & Future Work

This project serves as a research base for:

* **Task decomposition in real estate operations** using multi-agent systems.
* **Evaluation of deterministic vs. LLM-based ranking methods** for inventory matching.
* **Latency and cost trade-offs** when grounding LLMs on structured datasets.
* **Integrating multimodal inputs** (image recognition for property features).
* **Simulation of market behavior** by connecting leasing AI agents with synthetic tenant populations.

Future extensions:

* Fine-tuning SearchSpec extraction with domain-specific datasets.
* Adaptive ranking models using user feedback loops.
* Hybrid symbolic–neural reasoning for compliance-heavy document Q\&A.

---

## 9. Ethical and Privacy Considerations

* **PII Handling:** All sensitive inputs are session-bound in the open-source version.
* **Transparency:** Every LLM-generated output is explainable (scores, reasons, citations).
* **Bias Mitigation:** Ongoing evaluation for geographic and demographic fairness in recommendations.

---

## 10. Repository Structure

```
/frontend
    streamlit_app.py     # UI and session management
    components/          # Streamlit UI modules
/backend
    agents/              # Multi-agent pipeline code
    models/              # Pydantic data structures
    utils/               # CSV loading, scoring functions
/data
    buildings.csv        # Example building dataset
    units.csv            # Example unit dataset
/docs
    README.md            # Project overview
    research_notes.md    # Detailed research log
```

---

If you want, I can now **rewrite your main README.md** so that it starts with the normal project intro, then includes this research-heavy section as the “Technical Appendix”.

Do you want me to merge it like that? That would make your repo look like a serious research release.
