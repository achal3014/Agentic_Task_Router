"""
Wikipedia search tool — LangChain tool definition.
Retrieves concise summaries for factual and encyclopedic queries.
"""

import wikipedia
from langchain_core.tools import tool


@tool
def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia for factual and encyclopedic information.
    Use this for questions about people, concepts, history, science, or definitions.

    Args:
        query: The topic or question to search Wikipedia for

    Returns:
        A summary from Wikipedia or an error message
    """
    try:
        wikipedia.set_lang("en")
        summary = wikipedia.summary(query, sentences=5, auto_suggest=True)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        try:
            summary = wikipedia.summary(e.options[0], sentences=5)
            return summary
        except Exception:
            return f"Multiple results found for '{query}'. Could not resolve."
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for '{query}'."
    except Exception as e:
        return f"Wikipedia search failed: {str(e)}"
