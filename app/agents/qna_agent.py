from app.prompts.qna_prompt import QNA_PROMPT
from app.prompts.prompt_builder import build_prompt
from app.llm import call_llm


def answer_question(user_input: str) -> str:
    prompt = build_prompt(QNA_PROMPT, user_input)

    response = call_llm(
        prompt=prompt
    )

    return response["content"], response["tokens"], response["model"]
