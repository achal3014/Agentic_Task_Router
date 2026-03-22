from pydantic import BaseModel, Field
from typing import Literal, Optional, List


class RouterOutput(BaseModel):
    task_type: Literal["summarize", "qna", "translate", "research", "unsupported"]
    reasoning: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    tokens_used: Optional[int] = None


class APIRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None


class APIResponse(BaseModel):
    task_type: str
    response: str
    reasoning: str
    confidence: Optional[float] = None
    error: Optional[str] = None
    safety_flag: bool = False
    suspicion_flag: bool = False
    escalation_offer: Optional[bool] = None
    escalation_confirmed: Optional[bool] = None
    session_id: Optional[str] = None
    tools_called: Optional[List[str]] = None
    cost_usd: Optional[float] = None
