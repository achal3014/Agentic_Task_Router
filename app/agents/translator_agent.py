"""
Translation agent for converting text to English.

Translates text from any source language to English while preserving
meaning, tone, and structure without interpretation.
"""

from app.prompts.translator_prompt import TRANSLATOR_PROMPT
from app.prompts.prompt_builder import build_prompt
from app.llm import call_llm


def translate_text(user_input: str) -> tuple[str, int, str]:
    """
    Translates provided text to English.

    The agent:
    - Translates from any language to English only
    - Preserves meaning, tone, and structure exactly as they appear
    - Performs translation mechanically without interpretation
    - Maintains original formatting where possible
    - Refuses translation to non-English target languages

    Args:
        user_input: Text to translate (may include explicit "translate" instruction)

    Returns:
        tuple containing:
            - content (str): The translated English text
            - tokens (int): Number of tokens used
            - model (str): Name of the model used

    """
    prompt = build_prompt(TRANSLATOR_PROMPT, user_input)

    response = call_llm(prompt=prompt)

    return response["content"], response["tokens"], response["model"]
