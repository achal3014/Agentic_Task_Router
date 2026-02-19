from app.prompts.translator_prompt import TRANSLATOR_PROMPT
from app.prompts.prompt_builder import build_prompt
from app.llm import call_llm


def translate_text(user_input: str) -> tuple[str, int | None, str | None]:

    prompt = build_prompt(
        TRANSLATOR_PROMPT,
        user_input
    )

    response = call_llm(prompt=prompt)

    return response["content"], response["tokens"], response["model"]
