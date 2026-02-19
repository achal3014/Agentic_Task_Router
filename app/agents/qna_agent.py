"""
Question & Answer agent for document-grounded responses.

This agent answers questions strictly based on provided documentation
without using external knowledge or making recommendations.
"""

from app.prompts.qna_prompt import QNA_PROMPT
from app.prompts.prompt_builder import build_prompt
from app.llm import call_llm


def answer_question(user_input: str) -> tuple[str, int | None, str]:
    """
    Answers a question based strictly on provided documentation.

    The agent:
    - Only uses information from the provided document
    - Explicitly states when information is not available
    - Does not make recommendations or add external knowledge
    - Refuses to provide medical, legal, or financial advice

    Args:
        user_input: User query containing both question and document context

    Returns:
        Tuple of (answer_text, tokens_used, model_name)

    """
    prompt = build_prompt(QNA_PROMPT, user_input)

    response = call_llm(prompt=prompt)

    return response["content"], response["tokens"], response["model"]
