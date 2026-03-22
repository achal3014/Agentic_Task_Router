from typing import TypedDict, Optional, List, Annotated
import operator


def keep_last(a, b):
    """Always keep the latest value — used for all scalar fields."""
    return b if b is not None else a


class AgentState(TypedDict):
    user_input: str
    task_type: str
    safety_reason: Optional[str]
    routing_reasoning: str
    response: str
    error: Optional[str]
    safety_flag: bool
    suspicion_flag: bool
    model_used: Optional[str]
    tokens_used: Optional[int]
    confidence: Annotated[Optional[float], keep_last]
    escalation_confirmed: Annotated[Optional[bool], keep_last]
    escalation_offer: Annotated[Optional[bool], keep_last]
    session_id: Annotated[Optional[str], keep_last]
    conversation_history: Annotated[Optional[List[dict]], keep_last]
    retrieved_context: Annotated[Optional[str], keep_last]
    tools_called: Annotated[Optional[List[str]], keep_last]
    cost_usd: Annotated[Optional[float], lambda a, b: round((a or 0.0) + (b or 0.0), 6)]
