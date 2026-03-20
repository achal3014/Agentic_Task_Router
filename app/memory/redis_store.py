"""
Redis-based short-term conversational memory.

Stores and retrieves conversation history per session.
Each session holds an ordered list of turns (role + content).
TTL is applied on every write to keep sessions from persisting forever.
"""

import json
from typing import Optional
import redis
from app.configs import REDIS_HOST, REDIS_PORT, REDIS_TTL_SECONDS, HISTORY_TURNS


def _get_client() -> redis.Redis:
    """Returns a Redis client instance."""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def write_turn(session_id: str, role: str, content: str) -> None:
    """
    Appends a single turn to the session's conversation history.

    Args:
        session_id: Unique session identifier
        role: "user" or "assistant"
        content: The message content
    """
    client = _get_client()
    key = f"session:{session_id}:history"

    turn = json.dumps({"role": role, "content": content})
    client.rpush(key, turn)
    client.expire(key, REDIS_TTL_SECONDS)


def read_history(session_id: str, last_n: int = HISTORY_TURNS) -> list[dict]:
    """
    Retrieves the last N turns from the session's conversation history.

    Args:
        session_id: Unique session identifier
        last_n: Number of most recent turns to retrieve (default 6 = 3 exchanges)

    Returns:
        List of turn dicts with "role" and "content" keys
        Empty list if session doesn't exist
    """
    client = _get_client()
    key = f"session:{session_id}:history"

    raw_turns = client.lrange(key, -last_n, -1)
    return [json.loads(turn) for turn in raw_turns]


def clear_session(session_id: str) -> None:
    """
    Deletes all conversation history for a session.

    Args:
        session_id: Unique session identifier
    """
    client = _get_client()
    key = f"session:{session_id}:history"
    client.delete(key)
