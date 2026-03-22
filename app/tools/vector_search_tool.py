"""
Vector store search tool — LangChain tool definition.
Searches ChromaDB for semantically similar prior agent outputs.
"""

from langchain_core.tools import tool
from app.memory.vector_store import retrieve_context


@tool
def search_vector_store(query: str) -> str:
    """
    Search internal memory for prior relevant context.
    Use this to find related information from past conversations and agent outputs.
    Always call this first before other tools.

    Args:
        query: The search query to find semantically similar prior context

    Returns:
        Relevant prior context or empty string if nothing found
    """
    result = retrieve_context(query)
    if not result:
        return "No relevant prior context found in memory."
    return result
