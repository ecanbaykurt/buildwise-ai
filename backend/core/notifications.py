import json, time, uuid
from typing import Dict, Any, Optional

try:
    import redis  # optional
    r = redis.Redis.from_url("redis://localhost:6379/0")
except Exception:
    r = None

STREAM = "buildwise.events"

def publish_event(event_type: str, payload: Dict[str, Any], actor: str, conv_id: Optional[str]=None):
    evt = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "actor": actor,
        "conversation_id": conv_id,
        "payload": payload,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    if r:
        r.xadd(STREAM, {"data": json.dumps(evt)})
    return evt
