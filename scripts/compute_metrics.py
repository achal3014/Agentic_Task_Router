import json
import datetime
from collections import defaultdict

RESULTS_FILE = "scripts/evaluation_results.jsonl"
METRICS_OUTPUT_FILE = "scripts/evaluation_metrics.json"

# -------------------------
# Load results
# -------------------------
results = []
skipped = 0

with open(RESULTS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        entry = json.loads(line)
        if "id" in entry:
            results.append(entry)
        else:
            skipped += 1

if skipped:
    print(f"[WARNING] Skipped {skipped} metadata lines\n")

total_cases = len(results)
api_successes = [r for r in results if r.get("status") == "success"]
api_failures = [r for r in results if r.get("status") == "failed"]
valid_cases = len(api_successes)

# -------------------------
# 1. ROUTING ACCURACY
# -------------------------
correct_routing = 0
routing_failures = []

DEFAULT_REJECTION_ERROR = "Unsupported task."
SAFETY_BLOCK_ERROR = "Blocked by Tier-1 safety rules."

for r in api_successes:
    expected = r.get("expected_task")
    actual = r.get("actual_task")
    safety_flag = r.get("safety_flag")

    if safety_flag and expected == "unsupported":
        correct_routing += 1
    elif expected == actual:
        correct_routing += 1
    else:
        routing_failures.append(
            {"id": r.get("id"), "expected": expected, "actual": actual}
        )

routing_accuracy = correct_routing / valid_cases if valid_cases else 0

# -------------------------
# 2. TASK COMPLETION RATE
# -------------------------
completed_tasks = 0

for r in api_successes:
    expected = r.get("expected_task")
    actual = r.get("actual_task")
    error = r.get("error")
    response = r.get("response") or ""
    safety_flag = r.get("safety_flag")

    is_rejection = (
        error == DEFAULT_REJECTION_ERROR
        and expected == "unsupported"
        and actual == "unsupported"
    ) or (error == SAFETY_BLOCK_ERROR and safety_flag is True)

    if is_rejection:
        completed_tasks += 1
    elif error is None and response.strip():
        completed_tasks += 1

task_completion_rate = completed_tasks / valid_cases if valid_cases else 0

# -------------------------
# 3. COST PER QUERY
# -------------------------
costs = [r.get("cost_usd") for r in api_successes if r.get("cost_usd") is not None]
avg_cost = sum(costs) / len(costs) if costs else 0
total_cost = sum(costs)

cost_by_task = defaultdict(list)
for r in api_successes:
    if r.get("cost_usd") is not None:
        cost_by_task[r.get("actual_task", "unknown")].append(r["cost_usd"])

avg_cost_by_task = {task: round(sum(v) / len(v), 6) for task, v in cost_by_task.items()}

# -------------------------
# 4. MEMORY HIT RATE
# -------------------------
memory_hit_rate = 0
memory_hits = 0
memory_total = 0

try:
    import os

    LOG_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "logs",
        "decisions.json",
    )
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            log_entries = []
            for line in f:
                try:
                    log_entries.append(json.loads(line))
                except Exception:
                    pass

        for entry in log_entries:
            if entry.get("task_type") in ("qna", "research", "summarize"):
                memory_total += 1
                if entry.get("retrieved_context"):
                    memory_hits += 1

        memory_hit_rate = memory_hits / memory_total if memory_total else 0
    else:
        # Fallback — check memory/escalation sections for responses referencing prior context
        memory_section_cases = [
            r
            for r in api_successes
            if r.get("section") in ("memory_cross_session", "escalation_flow")
        ]
        context_hits = [
            r
            for r in memory_section_cases
            if r.get("response") and "prior" in (r.get("response") or "").lower()
        ]
        memory_total = len(memory_section_cases)
        memory_hits = len(context_hits)
        memory_hit_rate = memory_hits / memory_total if memory_total else 0

except Exception:
    memory_hit_rate = 0

# -------------------------
# 5. LATENCY PER AGENT
# -------------------------
latency_by_task = {}
try:
    import os

    LOG_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "logs",
        "decisions.json",
    )
    log_entries = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    log_entries.append(json.loads(line))
                except Exception:
                    pass

    latency_map = defaultdict(list)
    for entry in log_entries:
        if entry.get("latency_ms") and entry.get("task_type"):
            latency_map[entry["task_type"]].append(entry["latency_ms"])

    latency_by_task = {task: round(sum(v) / len(v)) for task, v in latency_map.items()}
except Exception:
    latency_by_task = {}

# -------------------------
# 6. TOOL USAGE RATE
# -------------------------
RESEARCH_TOOLS = {"wikipedia", "search_arxiv", "web_search"}

all_tools_called = []
for r in api_successes:
    tools = r.get("tools_called") or []
    all_tools_called.extend([t for t in tools if t in RESEARCH_TOOLS])

tool_counts = defaultdict(int)
for tool in all_tools_called:
    tool_counts[tool] += 1

total_research = len([r for r in api_successes if r.get("actual_task") == "research"])
tool_usage_rate = {
    tool: round(count / total_research, 4) if total_research else 0
    for tool, count in tool_counts.items()
}

# -------------------------
# PRINT SUMMARY
# -------------------------
print("=" * 60)
print("EVALUATION METRICS SUMMARY")
print("=" * 60)
print(f"\nTotal cases     : {total_cases}")
print(
    f"API success rate: {len(api_successes) / total_cases:.2%}  ({len(api_successes)}/{total_cases})"
)

print("\n--- 1. Routing Accuracy ---")
print(f"  {routing_accuracy:.2%}  ({correct_routing}/{valid_cases} correct)")
if routing_failures:
    for rf in routing_failures:
        print(
            f"  FAIL ID {rf['id']:>2} | expected={rf['expected']:<12} actual={rf['actual']}"
        )

print("\n--- 2. Task Completion Rate ---")
print(f"  {task_completion_rate:.2%}  ({completed_tasks}/{valid_cases} completed)")

print("\n--- 3. Cost Per Query ---")
print(f"  Average : ${avg_cost:.6f}")
print(f"  Total   : ${total_cost:.6f}")
for task, cost in sorted(avg_cost_by_task.items()):
    print(f"  {task:<12}: ${cost:.6f}")

print("\n--- 4. Memory Hit Rate ---")
print(
    f"  {memory_hit_rate:.2%}  ({memory_hits}/{memory_total} requests retrieved prior context)"
)

print("\n--- 5. Latency Per Agent (ms) ---")
if latency_by_task:
    for task, avg_ms in sorted(latency_by_task.items()):
        print(f"  {task:<12}: {avg_ms} ms avg")
else:
    print("  Enable logging (ENABLE_LOGGING=true) to capture latency data")

print("\n--- 6. Tool Usage Rate ---")
if tool_usage_rate:
    for tool, rate in sorted(tool_usage_rate.items()):
        print(f"  {tool:<20}: {rate:.2%} of research requests")
else:
    print("  No tool usage data found")

print("\n--- Section Breakdown ---")
sections = defaultdict(lambda: {"total": 0, "correct": 0})
for r in api_successes:
    section = r.get("section", "unknown")
    sections[section]["total"] += 1
    expected = r.get("expected_task")
    actual = r.get("actual_task")
    safety_flag = r.get("safety_flag")
    if (safety_flag and expected == "unsupported") or (expected == actual):
        sections[section]["correct"] += 1

for section, stats in sorted(sections.items()):
    acc = stats["correct"] / stats["total"] if stats["total"] else 0
    print(f"  {section:<25}: {acc:.1%}  ({stats['correct']}/{stats['total']})")

if api_failures:
    print("\n--- API Failures ---")
    for f in api_failures:
        print(f"  ID {f['id']:>2} | {f.get('error')}")

print("\n" + "=" * 60)

# -------------------------
# Save to JSON
# -------------------------
metrics_output = {
    "generated_at": datetime.datetime.now().isoformat(),
    "summary": {
        "total_cases": total_cases,
        "valid_cases": valid_cases,
        "api_success_rate": round(len(api_successes) / total_cases, 4)
        if total_cases
        else 0,
    },
    "metrics": {
        "routing_accuracy": round(routing_accuracy, 4),
        "task_completion_rate": round(task_completion_rate, 4),
        "cost_per_query": {
            "average_usd": round(avg_cost, 6),
            "total_usd": round(total_cost, 6),
            "by_task": avg_cost_by_task,
        },
        "memory_hit_rate": round(memory_hit_rate, 4),
        "latency_per_agent_ms": latency_by_task,
        "tool_usage_rate": tool_usage_rate,
    },
    "failures": {
        "api_failures": [
            {"id": f["id"], "error": f.get("error")} for f in api_failures
        ],
        "routing_failures": routing_failures,
    },
    "section_breakdown": {
        section: {
            "accuracy": round(stats["correct"] / stats["total"], 4)
            if stats["total"]
            else 0,
            "correct": stats["correct"],
            "total": stats["total"],
        }
        for section, stats in sorted(sections.items())
    },
}

with open(METRICS_OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(metrics_output, f, indent=4)

print(f"\nMetrics saved to {METRICS_OUTPUT_FILE}")
