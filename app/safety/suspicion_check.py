from app.constants.suspicious_patterns import SUSPICIOUS_PATTERNS


def suspicion_check(user_input: str) -> bool:
    lower_input = user_input.lower()

    for pattern in SUSPICIOUS_PATTERNS:
        if pattern in lower_input:
            return True

    return False
