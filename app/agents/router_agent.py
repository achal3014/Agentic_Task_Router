"""
Router agent for task classification and request routing.

This agent classifies user requests into one of the supported task types
(summarize, qna, translate, unsupported) using an LLM.
"""

import json
import os
from app.models import RouterOutput
from app.constants.tasks import SUPPORTED_TASKS, UNSUPPORTED_TASK
from app.llm import call_llm
from app.prompts.router_prompt import ROUTER_PROMPT

ROUTER_MODEL = os.getenv("GROQ_ROUTER_MODEL")


def route_task(user_input: str) -> RouterOutput:
    """
    Classifies user request into appropriate task type.

    Uses an LLM to analyze the request and determine which specialized
    agent should handle it. Returns structured output with task type
    and reasoning.

    Task types:
    - summarize: User wants text summarization
    - qna: User asks question with provided document
    - translate: User wants translation to English
    - unsupported: Invalid/unsupported request or multiple conflicting tasks

    Args:
        user_input: Raw user request text

    Returns:
        RouterOutput containing task_type and reasoning

    Raises:
        Returns UNSUPPORTED_TASK if JSON parsing fails or task type is invalid

    Example:
        >>> route_task("Summarize this: AI is...")
        RouterOutput(task_type="summarize", reasoning="Explicit summarize keyword")
    """
    full_prompt = f"""
{ROUTER_PROMPT}

User request:
{user_input}
"""

    # Override model ONLY here
    llm_response = call_llm(
        prompt=full_prompt,
        model=ROUTER_MODEL,
        temperature=0,
        max_tokens=100
    )

    raw_response = llm_response["content"]

    try:
        parsed = json.loads(raw_response)
        validated = RouterOutput(**parsed)

        if validated.task_type not in SUPPORTED_TASKS:
            return RouterOutput(
                task_type=UNSUPPORTED_TASK,
                reasoning="Router returned unsupported task."
            )

        return validated

    except Exception:
        return RouterOutput(
            task_type=UNSUPPORTED_TASK,
            reasoning="Invalid JSON from router model."
        )
