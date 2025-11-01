# utils/messages.py
from datetime import datetime
from typing import Any, Dict

def build_message(type_: str, status: str, payload: Any = None) -> Dict:
    """
    Standard message for pipelines

    :param type_: "pipeline" or "step"
    :param status: message state ("queued", "running", "error", "success", "ended", etc.)
    :param payload: additional message
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "type": type_,
        "status": status,
        "payload": payload or {},
    }
