from typing import List, Dict, Any
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI()

class LeaseAnswer(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    risk_flags: List[str] = []

SYSTEM = (
    "You answer strictly from retrieved lease text. Cite section and page. "
    "If the answer is not in the text, say 'Not found in provided lease' and suggest escalation."
)

class LeaseQAAgent:
    def run(self, question: str, retrieved_chunks: List[Dict[str, Any]]) -> LeaseAnswer:
        context = "\n\n".join([f"[{c.get('source','doc')} p{c.get('page', '?')}] {c['text']}" for c in retrieved_chunks])
        messages = [
            {"role":"system","content":SYSTEM},
            {"role":"user","content": f"Lease snippets:\n{context}\n\nQuestion: {question}\nProvide a concise answer with inline citations."}
        ]
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        txt = resp.choices[0].message.content
        # simple placeholder citation extraction
        cits = [{"section":"unknown","page": c.get("page")} for c in retrieved_chunks[:2]]
        return LeaseAnswer(answer=txt, citations=cits)
