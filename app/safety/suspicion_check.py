import json
from app.constants.suspicious_patterns import SUSPICIOUS_PATTERNS
from app.prompts.semantic_safety_prompt import SEMANTIC_SAFETY_PROMPT
from app.llm import call_llm
from app.configs import ROUTER_MODEL


def suspicion_check(user_input: str) -> bool:
    """
    Two-stage suspicion check:

    Stage 1 — Keyword matching (fast, no LLM call):
        If any known suspicious pattern is found, return True immediately.

    Stage 2 — LLM semantic check (slower, catches implicit cases):
        If keywords don't flag it, ask the LLM to evaluate intent.
        Returns True if LLM considers it suspicious.

    Falls back to False if LLM call fails — suspicion check is a
    soft flag and should never block the request on its own.
    """

    # Stage 1 — keyword check
    lower_input = user_input.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern in lower_input:
            return True

    # Stage 2 — LLM semantic check
    try:
        full_prompt = f"""
{SEMANTIC_SAFETY_PROMPT}

User input:
{user_input}
"""

        llm_response = call_llm(
            prompt=full_prompt, model=ROUTER_MODEL, temperature=0, max_tokens=50
        )

        raw = llm_response["content"].strip()

        # Strip markdown fences if model wraps response
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)
        return bool(parsed.get("suspicious", False))

    except Exception:
        # Soft flag — never block on failure
        return False
