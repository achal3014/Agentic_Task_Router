import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
groq_model = os.getenv("GROQ_MAIN_MODEL")
groq_fallback_model = os.getenv("GROQ_FALLBACK_MODEL")


class LLMServiceError(Exception):
    """Custom exception for LLM failures."""
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True
)
def _invoke_groq(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int
) -> dict:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )

    return {
        "content": response.choices[0].message.content,
        "model": model,
        "tokens": getattr(response.usage, "total_tokens", None)
    }


def call_llm(
    prompt: str,
    model: str | None = None,
    temperature: float = 0,
    max_tokens: int = 300
) -> dict:
    """
    Calls Groq with fallback support.
    """

    primary_model = model or groq_model

    # 1️⃣ Try primary model
    try:
        result = _invoke_groq(prompt, primary_model, temperature, max_tokens)
        print(f"[LLM] Using model: {result['model']}")
        return result

    except Exception as primary_error:
        # 2️⃣ Try fallback model
        try:
            result = _invoke_groq(
                prompt, groq_fallback_model, temperature, max_tokens)
            print(f"[LLM] Using FALLBACK model: {result['model']}")
            return result
        except Exception as fallback_error:
            raise LLMServiceError(
                f"Primary model failed: {primary_error} | "
                f"Fallback model failed: {fallback_error}"
            )
