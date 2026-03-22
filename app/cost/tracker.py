"""
Cost tracker — calculates USD cost from token usage per LLM call.
Reads pricing constants from configs.ini [COST] section.
"""

from app.configs import (
    COST_PER_1K_TOKENS_MAIN,
    COST_PER_1K_TOKENS_FALLBACK,
    COST_PER_1K_TOKENS_ROUTER,
    ROUTER_MODEL,
    FALLBACK_MODEL,
)


MODEL_COST_MAP = {
    ROUTER_MODEL: COST_PER_1K_TOKENS_ROUTER,
    FALLBACK_MODEL: COST_PER_1K_TOKENS_FALLBACK,
}


def calculate_cost(model: str, tokens_used: int) -> float:
    """
    Calculates cost in USD for a single LLM call.

    Args:
        model: Model name used for the call
        tokens_used: Total tokens consumed

    Returns:
        Cost in USD rounded to 6 decimal places
    """
    if not tokens_used or not model:
        return 0.0

    cost_per_1k = MODEL_COST_MAP.get(model, COST_PER_1K_TOKENS_MAIN)
    cost = (tokens_used / 1000) * cost_per_1k
    return round(cost, 6)


def accumulate_cost(existing: float, new_cost: float) -> float:
    """
    Adds new cost to existing accumulated cost.

    Args:
        existing: Previously accumulated cost
        new_cost: Cost from latest LLM call

    Returns:
        Updated total cost
    """
    return round((existing or 0.0) + new_cost, 6)
