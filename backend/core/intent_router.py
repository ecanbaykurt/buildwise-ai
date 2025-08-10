from typing import Literal

def route_intent(user_text: str) -> Literal["VIA","DOMA"]:
    text = user_text.lower()
    via_triggers = ["find","search","available","tour","listings","units"]
    if any(t in text for t in via_triggers):
        return "VIA"
    return "DOMA"
