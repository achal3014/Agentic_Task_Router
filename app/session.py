"""
Session identity management.

Generates a new session ID if the client doesn't provide one.
Validates incoming session IDs for correct format.
"""

import uuid
from typing import Optional


def get_or_create_session_id(session_id: Optional[str] = None) -> str:
    """
    Returns the provided session ID if valid, otherwise generates a new one.

    Args:
        session_id: Session ID from the client request, or None

    Returns:
        Valid session ID string
    """
    if session_id and is_valid_session_id(session_id):
        return session_id
    return str(uuid.uuid4())


def is_valid_session_id(session_id: str) -> bool:
    """
    Validates that a session ID is a properly formatted UUID.

    Args:
        session_id: Session ID string to validate

    Returns:
        True if valid UUID format, False otherwise
    """
    try:
        uuid.UUID(session_id)
        return True
    except ValueError:
        return False
