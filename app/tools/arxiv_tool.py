"""
ArXiv search tool — LangChain tool definition.
Retrieves abstracts from recent relevant academic papers.
No API key required.
"""

import arxiv
from langchain_core.tools import tool


@tool
def search_arxiv(query: str) -> str:
    """
    Search ArXiv for academic papers and research publications.
    Use this for questions about latest research, scientific topics,
    technical papers, AI advancements, or any topic that benefits
    from peer-reviewed academic sources.

    Args:
        query: The research topic or question to search papers for

    Returns:
        Formatted string of paper titles, authors, and abstracts
    """
    try:
        client = arxiv.Client()

        # Search with relevance first
        relevance_search = arxiv.Search(
            query=query,
            max_results=5,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        # Search with recency
        recency_search = arxiv.Search(
            query=query,
            max_results=5,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )

        relevance_results = list(client.results(relevance_search))
        recency_results = list(client.results(recency_search))

        # Merge — deduplicate by paper ID, prefer recent if overlap
        seen_ids = set()
        merged = []

        for paper in recency_results + relevance_results:
            paper_id = paper.entry_id
            if paper_id not in seen_ids:
                seen_ids.add(paper_id)
                merged.append(paper)
            if len(merged) >= 5:
                break

        if not merged:
            return f"No ArXiv papers found for '{query}'."

        formatted = []
        for i, paper in enumerate(merged, 1):
            authors = ", ".join(a.name for a in paper.authors[:3])
            if len(paper.authors) > 3:
                authors += " et al."
            published = (
                paper.published.strftime("%Y-%m-%d")
                if paper.published
                else "Unknown date"
            )
            formatted.append(
                f"[Paper {i}] {paper.title}\n"
                f"Authors: {authors} | Published: {published}\n"
                f"Abstract: {paper.summary[:500]}{'...' if len(paper.summary) > 500 else ''}"
            )

        return "\n\n".join(formatted)

    except Exception as e:
        return f"ArXiv search failed: {str(e)}"
