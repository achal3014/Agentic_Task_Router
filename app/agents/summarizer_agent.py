"""
Summarizer agent for text condensation and key point extraction.

This agent generates clear, concise summaries of provided text without
adding interpretations or external information.
"""

from app.prompts.summarizer_prompt import SUMMARIZER_PROMPT
from app.prompts.prompt_builder import build_prompt
from app.llm import call_llm


CONVERSATION_KEYWORDS = [
    "our conversation",
    "our chat",
    "what we discussed",
    "conversation so far",
    "chat so far",
    "what was discussed",
    "summarize this conversation",
    "summarize our session",
]


def summarize_text(state: dict) -> tuple[str, int | None, str]:
    """
    Generates a concise summary of provided text.

    If the user asks to summarize the conversation, feeds Redis history
    as the document instead of just the user input.

    Args:
        state: Full agent state containing user_input and conversation_history

    Returns:
        Tuple of (summary_text, tokens_used, model_name)
    """
    user_input = state.get("user_input", "")
    history = state.get("conversation_history") or []

    # Check if user wants to summarize the conversation
    is_conversation_summary = any(
        kw in user_input.lower() for kw in CONVERSATION_KEYWORDS
    )

    if is_conversation_summary and history:
        # Format conversation history as the document to summarize
        formatted = "\n".join(
            f"{t['role'].upper()}: {t['content'][:500]}" for t in history
        )
        content_to_summarize = f"Summarize the following conversation:\n\n{formatted}"
    else:
        content_to_summarize = user_input

    prompt = build_prompt(SUMMARIZER_PROMPT, content_to_summarize)
    response = call_llm(prompt=prompt)

    return response["content"], response.get("tokens_used"), response.get("model")
