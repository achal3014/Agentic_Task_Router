"""
Research Agent — answers open-ended knowledge questions
from training knowledge.

Tools and memory will be added in later features.
"""

from app.llm import call_llm
from app.prompts.research_prompt import RESEARCH_PROMPT
from app.prompts.system_policy import SYSTEM_POLICY
from app.configs import MAIN_MODEL, TEMPERATURE, MAX_TOKENS, HISTORY_TURNS


def run_research(state: dict) -> tuple[str, int, str]:
    user_input = state.get("user_input", "")
    history = state.get("conversation_history") or []

    # Build prior context from history
    history_context = ""
    if history:
        recent = history[-HISTORY_TURNS:]
        lines = "\n".join(f"{t['role'].upper()}: {t['content'][:300]}" for t in recent)
        history_context = f"""
Prior conversation context:
{lines}

Based on the above conversation, provide a deeper and more comprehensive answer.
"""

    full_prompt = f"""
{SYSTEM_POLICY}

{RESEARCH_PROMPT}

{history_context}
USER REQUEST:
{user_input}
"""

    result = call_llm(
        prompt=full_prompt,
        model=MAIN_MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )

    return result["content"], result.get("tokens_used"), result.get("model")
