"""
DuckDuckGo web search tool — LangChain tool definition.
Retrieves current web results for open-ended queries.
No API key required.
"""

from ddgs import DDGS
from langchain_core.tools import tool


@tool
def search_web(query: str) -> str:
    """
    Search the web using DuckDuckGo for current or broad topics.
    Use this for recent news, trends, current events, or topics
    that need up-to-date information beyond training knowledge.

    Args:
        query: The search query string

    Returns:
        Formatted web search results or an error message
    """
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                title = r.get("title", "No title")
                body = r.get("body", "No content")
                url = r.get("href", "")
                results.append(f"[{title}] ({url}): {body}")

        if not results:
            return f"No web results found for '{query}'."

        return "\n\n".join(results)

    except Exception as e:
        return f"Web search failed: {str(e)}"
