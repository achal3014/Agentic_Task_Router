"""
Memory manager — coordinates Redis and ChromaDB.

Decides what gets written where:
- All turns → Redis (short-term, session-scoped)
- Meaningful outputs → ChromaDB (long-term, semantic)

Meaningful outputs: qna, research, summarize responses.
Not stored: errors, refusals, unsupported, very short responses.

Storage behavior:
- Near-duplicates are overwritten not appended (handled in vector_store.py)
- Responses are summarized before storage to reduce noise
- Topic changes are detected at retrieval time to avoid irrelevant context
"""

from app.configs import ENABLE_MEMORY

STORABLE_TASKS = ["qna", "research", "summarize"]
MIN_RESPONSE_LENGTH = 100  # responses shorter than this aren't worth storing


def should_store_in_vector(task_type: str, response: str, error: str) -> bool:
    """
    Decides whether a response is worth storing in ChromaDB.

    Stricter than before:
    - Must be a storable task type
    - Must have no error
    - Must be long enough to be meaningful
    - Memory must be enabled

    Args:
        task_type: The agent that produced the response
        response: The response text
        error: Any error string from state

    Returns:
        True if the response should be stored
    """
    if not ENABLE_MEMORY:
        return False
    if error:
        return False
    if not response or not response.strip():
        return False
    if len(response.strip()) < MIN_RESPONSE_LENGTH:
        return False
    if task_type not in STORABLE_TASKS:
        return False
    return True
