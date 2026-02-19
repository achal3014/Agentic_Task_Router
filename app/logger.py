import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any
from app.state import AgentState

# Absolute-safe log path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(BASE_DIR, "logs", "decisions.json")


def log_decision(
    state: AgentState,
    latency_ms: int
) -> Dict[str, Any]:
    """
    Generates a structured audit log for a single request.
    """

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": str(uuid.uuid4()),

        "user_input": state.get("user_input"),
        "task_type": state.get("task_type"),
        "safety_reason": state.get("safety_reason"),
        "routing_reasoning": state.get("routing_reasoning"),


        "safety_flag": state.get("safety_flag"),
        "suspicion_flag": state.get("suspicion_flag"),

        "response": state.get("response"),
        "error": state.get("error"),

        "model_used": state.get("model_used"),
        "tokens_used": state.get("tokens_used"),
        "latency_ms": latency_ms
    }

    # Ensure logs directory exists
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    # Append log entry
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + "\n")

    return log_entry
