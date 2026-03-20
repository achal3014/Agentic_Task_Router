"""
Router agent for task classification and request routing.

Classifies user requests into one of:
summarize, qna, translate, research, unsupported.

Uses LLM for intelligent classification with confidence scoring.
Reads conversation history from state for context-aware routing.
"""

import json
from app.models import RouterOutput
from app.constants.tasks import SUPPORTED_TASKS, UNSUPPORTED_TASK
from app.llm import call_llm
from app.prompts.router_prompt import ROUTER_PROMPT
from app.configs import (
    ROUTER_MODEL,
    ROUTER_TEMPERATURE,
    ROUTER_MAX_TOKENS,
    HISTORY_TURNS,
)


def route_task(state: dict) -> RouterOutput:
    """
    Classifies user request into appropriate task type.
    Reads conversation history from state for context-aware routing.

    Args:
        state: Full agent state containing user_input and conversation_history

    Returns:
        RouterOutput with task_type, reasoning, confidence
    """
    user_input = state.get("user_input", "")
    history = state.get("conversation_history") or []

    # Build history context string if history exists
    history_context = ""
    if history:
        recent = history[-HISTORY_TURNS:]
        lines = "\n".join(f"{t['role'].upper()}: {t['content'][:200]}" for t in recent)
        history_context = f"""
Recent conversation (use this to understand follow-up intent):
{lines}

"""

    full_prompt = f"""
{ROUTER_PROMPT}

{history_context}User request:
{user_input}
"""

    try:
        llm_response = call_llm(
            prompt=full_prompt,
            model=ROUTER_MODEL,
            temperature=ROUTER_TEMPERATURE,
            max_tokens=ROUTER_MAX_TOKENS,
        )

        raw_response = llm_response.get("content", "").strip()

        # Handle markdown-wrapped JSON
        if raw_response.startswith("```"):
            parts = raw_response.split("```")
            if len(parts) > 1:
                raw_response = parts[1]
                if raw_response.startswith("json"):
                    raw_response = raw_response[4:]
            raw_response = raw_response.strip()

        parsed = json.loads(raw_response)
        validated = RouterOutput(**parsed)

        if validated.task_type not in SUPPORTED_TASKS:
            return RouterOutput(
                task_type=UNSUPPORTED_TASK,
                reasoning="Router returned unsupported task.",
                confidence=validated.confidence,
            )

        return validated

    except Exception as e:
        print("ROUTER ERROR")
        print("User Input:", user_input)
        print("Raw Response:", raw_response if "raw_response" in locals() else "N/A")
        print("Error:", str(e))

        return RouterOutput(
            task_type=UNSUPPORTED_TASK,
            reasoning="Router failed to parse response.",
            confidence=0.0,
        )
