"""
ChromaDB-based long-term semantic memory.

Stores meaningful agent outputs as embeddings.
Retrieves semantically similar prior context for new requests.

Improvements:
- Deduplication: near-duplicate entries are replaced not appended
- Topic change detection: skips retrieval when query is semantically unrelated
- Summaries stored instead of full responses (summarization done upstream in graph.py)
"""

import uuid
import chromadb
from datetime import datetime
from chromadb.utils import embedding_functions
from app.configs import (
    VECTOR_STORE_PATH,
    EMBEDDING_MODEL,
    SIMILARITY_THRESHOLD,
    TOPIC_CHANGE_THRESHOLD,
)

_client = None
_collection = None


def _get_collection():
    """
    Returns the ChromaDB collection, initializing if needed.
    Singleton pattern — only one client and collection instance.
    """
    global _client, _collection

    if _collection is not None:
        return _collection

    _client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    _collection = _client.get_or_create_collection(
        name="agent_outputs", embedding_function=ef
    )

    return _collection


def _find_duplicate(text: str) -> str | None:
    """
    Checks if a near-duplicate of the given text already exists in the collection.
    Uses ChromaDB's built-in embedding function for querying.

    Args:
        text: The document text to check for duplicates

    Returns:
        ID of the duplicate document if found, None otherwise
    """
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return None

    results = collection.query(query_texts=[text], n_results=1, include=["distances"])

    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]

    if not distances or not ids:
        return None

    similarity = 1 / (1 + distances[0])

    if similarity >= SIMILARITY_THRESHOLD:
        return ids[0]

    return None


def store_output(
    session_id: str, task_type: str, user_input: str, response: str
) -> None:
    """
    Embeds and stores an agent output in ChromaDB.
    Overwrites near-duplicates instead of appending.
    Expects a summarized response — summarization done upstream in graph.py.

    Args:
        session_id: Session identifier for metadata
        task_type: Type of task that produced this output
        user_input: The original user query
        response: The summarized agent response to store
    """
    collection = _get_collection()

    # Check for near-duplicate and overwrite if found
    duplicate_id = _find_duplicate(response)
    if duplicate_id:
        collection.delete(ids=[duplicate_id])
        print(f"[vector_store] Replaced near-duplicate entry {duplicate_id[:8]}...")

    doc_id = str(uuid.uuid4())
    collection.add(
        ids=[doc_id],
        documents=[response],
        metadatas=[
            {
                "session_id": session_id,
                "task_type": task_type,
                "user_input": user_input[:500],
                "timestamp": datetime.utcnow().isoformat(),
            }
        ],
    )


def retrieve_context(query: str, n_results: int = 3) -> str:
    """
    Searches ChromaDB for semantically similar prior outputs.
    Skips retrieval if the query is semantically unrelated to stored content.

    Args:
        query: The current user input to search against
        n_results: Number of results to retrieve

    Returns:
        Formatted string of relevant prior context,
        or empty string if nothing relevant found or topic has changed
    """
    collection = _get_collection()

    count = collection.count()
    if count == 0:
        return ""

    actual_n = min(n_results, count)

    results = collection.query(
        query_texts=[query],
        n_results=actual_n,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return ""

    # Topic change detection — check best match similarity
    if distances:
        best_similarity = 1 / (1 + distances[0])
        print(best_similarity)
        if best_similarity < TOPIC_CHANGE_THRESHOLD:
            print(
                f"[vector_store] Topic change detected (similarity={best_similarity:.2f}) — skipping retrieval"
            )
            return ""

    context_parts = []
    for doc, meta in zip(documents, metadatas):
        task = meta.get("task_type", "unknown")
        original_query = meta.get("user_input", "")
        context_parts.append(
            f"[Prior {task} response to '{original_query[:100]}']: {doc[:300]}"
        )

    return "\n\n".join(context_parts)
