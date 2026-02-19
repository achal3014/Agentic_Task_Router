from app.constants.blocked_keywords import BLOCKED_KEYWORDS


def safety_check(user_input: str) -> dict:
    lower_input = user_input.lower()

    for keyword in BLOCKED_KEYWORDS:
        if keyword in lower_input:
            return {
                "blocked": True,
                "reason": f"Blocked due to restricted topic: {keyword}"
            }

    return {
        "blocked": False,
        "reason": None
    }
