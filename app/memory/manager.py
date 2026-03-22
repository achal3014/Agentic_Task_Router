"""
Memory manager — coordinates Redis and ChromaDB.

Decides what gets written where:
- All turns → Redis (short-term, session-scoped)
- Meaningful outputs → ChromaDB (long-term, semantic)

Meaningful outputs: qna, research, summarize responses.
Not stored: errors, refusals, unsupported responses.
"""

from app.configs import ENABLE_MEMORY

STORABLE_TASKS = ["qna", "research", "summarize"]


def should_store_in_vector(task_type: str, response: str, error: str) -> bool:
    """
    Decides whether a response is worth storing in ChromaDB.
    """
    if not ENABLE_MEMORY:
        return False
    if error:
        return False
    if not response or not response.strip():
        return False
    if task_type not in STORABLE_TASKS:
        return False
    return True
