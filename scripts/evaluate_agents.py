import requests
import json
import time
from datetime import datetime
from eval_cases import EVAL_CASES

API_URL = "http://127.0.0.1:8000/route"
OUTPUT_FILE = "scripts/evaluation_results.jsonl"

# -----------------------------
# Write run metadata
# -----------------------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(json.dumps({
        "run_started_at": datetime.utcnow().isoformat()
    }) + "\n")

# -----------------------------
# Execute Evaluation
# -----------------------------
for case in EVAL_CASES:
    try:
        response = requests.post(
            API_URL,
            json={"user_input": case["query"]},
            timeout=30
        )

        # Check if response is valid JSON
        output = response.json()

        # API call succeeded
        result = {
            "id": case["id"],
            "query": case["query"],
            "expected_task": case["expected_task"],
            "actual_task": output.get("task_type", ""),
            "expected_behavior": case["expected_behavior"],
            "response": output.get("response"),
            "error": output.get("error"),
            "safety_flag": output.get("safety_flag"),
            "suspicion_flag": output.get("suspicion_flag"),
            "status": "success",  # API call worked
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        # API call failed (connection error, timeout, invalid JSON, etc.)
        result = {
            "id": case["id"],
            "query": case["query"],
            "expected_task": case["expected_task"],
            "expected_behavior": case["expected_behavior"],
            "actual_task": None,
            "response": None,
            "error": str(e),
            "safety_flag": None,
            "suspicion_flag": None,
            "status": "failed",  # API call failed
            "timestamp": datetime.utcnow().isoformat()
        }

    # Persist immediately (crash-safe)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(result) + "\n")

    print(f"Evaluated case {case['id']} → API call {result['status']}")
    time.sleep(0.5)

print(f"\nEvaluation completed. Results saved to {OUTPUT_FILE}")
print("Run compute_metrics.py to see detailed breakdown.")
