from pydantic import BaseModel
from typing import Literal, Optional


class RouterOutput(BaseModel):
    task_type: Literal["summarize", "qna", "translate", "unsupported"]
    reasoning: str


class APIRequest(BaseModel):
    user_input: str


class APIResponse(BaseModel):
    task_type: str
    response: str
    reasoning: str
    error: Optional[str] = None
    safety_flag: bool = False        # ← Make sure these fields exist
    suspicion_flag: bool = False     # ← Make sure these fields exist
