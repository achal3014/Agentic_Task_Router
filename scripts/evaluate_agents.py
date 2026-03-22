import requests
import json
import time
from datetime import datetime
from eval_cases import EVAL_CASES, ESCALATION_SESSION_ID, MEMORY_SESSION_ID

API_URL = "http://127.0.0.1:8000/route"
OUTPUT_FILE = "scripts/evaluation_results.jsonl"

# -----------------------------
# Write run metadata
# -----------------------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(json.dumps({"run_started_at": datetime.utcnow().isoformat()}) + "\n")

# -----------------------------
# Execute Evaluation
# -----------------------------
for case in EVAL_CASES:
    # Resolve session ID
    session_id = None
    if case.get("session_id") == "ESCALATION_SESSION":
        session_id = ESCALATION_SESSION_ID
    elif case.get("session_id") == "MEMORY_SESSION":
        session_id = MEMORY_SESSION_ID

    # Build request payload
    payload = {"user_input": case["query"]}
    if session_id:
        payload["session_id"] = session_id

    try:
        response = requests.post(API_URL, json=payload, timeout=60)

        output = response.json()

        result = {
            "id": case["id"],
            "query": case["query"],
            "section": case.get("section"),
            "expected_task": case["expected_task"],
            "actual_task": output.get("task_type", ""),
            "expected_behavior": case["expected_behavior"],
            "response": output.get("response"),
            "error": output.get("error"),
            "safety_flag": output.get("safety_flag"),
            "suspicion_flag": output.get("suspicion_flag"),
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            # new fields
            "confidence": output.get("confidence"),
            "escalation_offer": output.get("escalation_offer"),
            "escalation_confirmed": output.get("escalation_confirmed"),
            "tools_called": output.get("tools_called"),
            "cost_usd": output.get("cost_usd"),
            "session_id": output.get("session_id"),
        }

    except Exception as e:
        result = {
            "id": case["id"],
            "query": case["query"],
            "section": case.get("section"),
            "expected_task": case["expected_task"],
            "expected_behavior": case["expected_behavior"],
            "actual_task": None,
            "response": None,
            "error": str(e),
            "safety_flag": None,
            "suspicion_flag": None,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": None,
            "escalation_offer": None,
            "escalation_confirmed": None,
            "tools_called": None,
            "cost_usd": None,
            "session_id": None,
        }

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(result) + "\n")

    print(
        f"Evaluated case {case['id']:>2} [{case['section']:<22}] → {result['status']}"
    )
    time.sleep(0.5)

print(f"\nEvaluation completed. Results saved to {OUTPUT_FILE}")
print("Run compute_metrics.py to see detailed breakdown.")
