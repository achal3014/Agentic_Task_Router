from typing import TypedDict, Optional


class AgentState(TypedDict):
    user_input: str
    task_type: str
    safety_reason: Optional[str]
    routing_reasoning: str
    response: str
    error: Optional[str]
    safety_flag: bool          # hard block
    suspicion_flag: bool     # soft semantic flag
    model_used: Optional[str]
    tokens_used: Optional[int]
