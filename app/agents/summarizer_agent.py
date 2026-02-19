from app.prompts.summarizer_prompt import SUMMARIZER_PROMPT
from app.prompts.prompt_builder import build_prompt
from app.llm import call_llm


def summarize_text(user_input: str) -> tuple[str, int | None]:
    prompt = build_prompt(SUMMARIZER_PROMPT, user_input)

    response = call_llm(prompt=prompt)

    return response["content"], response["tokens"], response["model"]
