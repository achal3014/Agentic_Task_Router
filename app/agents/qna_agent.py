"""
Question & Answer agent for document-grounded responses.

This agent answers questions strictly based on provided documentation
without using external knowledge or making recommendations.
"""

from app.prompts.qna_prompt import QNA_PROMPT
from app.prompts.prompt_builder import build_prompt
from app.llm import call_llm


def answer_question(state: dict) -> tuple[str, int, str]:
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

    user_input = state.get("user_input", "")
    retrieved_context = state.get("retrieved_context", "")

    context_block = ""
    if retrieved_context:
        context_block = f"""
            Relevant prior context from memory:
            {retrieved_context}

            Use this context to give a more informed answer if relevant.
            """

    prompt = build_prompt(QNA_PROMPT, f"{context_block}{user_input}")

    response = call_llm(prompt=prompt)

    return response["content"], response.get("tokens_used"), response.get("model")
