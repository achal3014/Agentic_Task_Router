"""
ChromaDB-based long-term semantic memory.

Stores meaningful agent outputs as embeddings.
Retrieves semantically similar prior context for new requests.
"""

import chromadb
from chromadb.utils import embedding_functions
from app.configs import VECTOR_STORE_PATH, EMBEDDING_MODEL

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


def store_output(
    session_id: str, task_type: str, user_input: str, response: str
) -> None:
    """
    Embeds and stores an agent output in ChromaDB.
    Only meaningful outputs are stored — not errors or refusals.

    Args:
        session_id: Session identifier for metadata
        task_type: Type of task that produced this output
        user_input: The original user query
        response: The agent's response to store
    """
    collection = _get_collection()

    import uuid
    from datetime import datetime

    doc_id = str(uuid.uuid4())

    # Store the response text as the document
    # User input stored as metadata for context
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

    Args:
        query: The current user input to search against
        n_results: Number of results to retrieve

    Returns:
        Formatted string of relevant prior context,
        or empty string if nothing relevant found
    """
    collection = _get_collection()

    # Need at least n_results documents in collection
    count = collection.count()
    if count == 0:
        return ""

    actual_n = min(n_results, count)

    results = collection.query(query_texts=[query], n_results=actual_n)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        return ""

    context_parts = []
    for doc, meta in zip(documents, metadatas):
        task = meta.get("task_type", "unknown")
        original_query = meta.get("user_input", "")
        context_parts.append(
            f"[Prior {task} response to '{original_query[:100]}']: {doc[:300]}"
        )

    return "\n\n".join(context_parts)
