"""
Summarizer agent for text condensation and key point extraction.

This agent generates clear, concise summaries of provided text without
adding interpretations or external information.
"""

from app.prompts.summarizer_prompt import SUMMARIZER_PROMPT
from app.prompts.prompt_builder import build_prompt
from app.llm import call_llm


def summarize_text(user_input: str) -> tuple[str, int | None, str]:
    """
    Generates a concise summary of provided text.

    The agent:
    - Focuses on main ideas and key points
    - Uses clear, beginner-friendly language
    - Preserves original meaning without interpretation
    - Does not add opinions or recommendations

    Args:
        user_input: Text to be summarized (with or without "summarize" instruction)

    Returns:
        Tuple of (summary_text, tokens_used, model_name)

    """
    prompt = build_prompt(SUMMARIZER_PROMPT, user_input)

    response = call_llm(prompt=prompt)

    return response["content"], response["tokens"], response["model"]
