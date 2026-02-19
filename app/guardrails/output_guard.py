import os
from guardrails import Guard
from guardrails.hub import ProfanityFree, DetectPII

# Configuration
GUARDRAILS_ENABLED = os.getenv("GUARDRAILS_ENABLED", "true").lower() == "true"

# -------------------------
# Lazy initialization - only create guards when needed
# -------------------------

_profanity_guard = None
_pii_guard = None


def _get_profanity_guard():
    """Lazy load profanity guard only when needed"""
    global _profanity_guard
    if _profanity_guard is None:
        _profanity_guard = Guard().use(ProfanityFree(on_fail="exception"))
    return _profanity_guard


def _get_pii_guard():
    """Lazy load PII guard only when needed"""
    global _pii_guard
    if _pii_guard is None:
        _pii_guard = Guard().use(DetectPII(on_fail="exception"))
    return _pii_guard


def check_profanity(text: str) -> dict:
    try:
        _get_profanity_guard().validate(text)
        return {"allowed": True, "reason": None}
    except Exception:
        return {"allowed": False, "reason": "Profanity detected"}


def check_pii(text: str) -> dict:
    try:
        _get_pii_guard().validate(text)
        return {"allowed": True, "reason": None}
    except Exception:
        return {"allowed": False, "reason": "PII detected"}


def validate_output(text: str) -> dict:
    """
    Runs all output guards.
    Fails fast on first violation.
    Can be toggled via GUARDRAILS_ENABLED environment variable.

    Returns:
        dict with 'allowed' (bool) and 'reason' (str or None)
    """
    # Early exit if disabled - NO guard initialization happens
    if not GUARDRAILS_ENABLED:
        return {"allowed": True, "reason": None}

    if not text or not text.strip():
        return {"allowed": True, "reason": None}

    # Guards only created here if enabled
    profanity_result = check_profanity(text)
    if not profanity_result["allowed"]:
        return profanity_result

    pii_result = check_pii(text)
    if not pii_result["allowed"]:
        return pii_result

    return {"allowed": True, "reason": None}


def get_guardrails_status() -> dict:
    """Returns current guardrails configuration status."""
    return {
        "enabled": GUARDRAILS_ENABLED,
        "validators": ["ProfanityFree", "DetectPII"] if GUARDRAILS_ENABLED else []
    }
