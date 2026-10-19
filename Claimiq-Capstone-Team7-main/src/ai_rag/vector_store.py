"""
vector_store.py (ai_rag module)

Purpose: Thin wrapper around ChromaDB - the ONLY file that knows
HOW we talk to the vector store. If we ever swap to Azure AI Search
or another vector DB later, this is the only file that changes.
"""

import chromadb
from pathlib import Path

# Persistent local storage - survives app restarts (unlike in-memory mode)
CHROMA_PATH = Path("data/chroma_db")
CHROMA_PATH.mkdir(parents=True, exist_ok=True)

_client = chromadb.PersistentClient(path=str(CHROMA_PATH))

COLLECTION_NAME = "policy_documents"


def get_collection():
    """
    Returns the single Chroma 'collection' (think: table) we use for
    all policy/guideline document chunks across the whole system.
    """
    return _client.get_or_create_collection(name=COLLECTION_NAME,metadata={"hnsw:space": "cosine"})


def add_chunks(
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict],
) -> None:
    """
    Stores chunk vectors + text + metadata together.
    - ids: unique chunk identifiers (we'll use f"{document_id}_{chunk_index}")
    - embeddings: the vectors from Azure OpenAI
    - documents: the actual chunk text (Chroma's term for the raw content)
    - metadatas: dicts like {"document_id": ..., "document_title": ..., "chunk_index": ...}
    """
    collection = get_collection()
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )


def query_similar_chunks(query_embedding: list[float], top_k: int = 4) -> dict:
    """
    Searches for the top_k most similar chunks to the given query vector.
    Returns Chroma's raw result dict, containing documents, metadatas,
    distances (lower = more similar), and ids.
    """
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )
    return results


def delete_chunks_by_document_id(document_id: str) -> None:
    """
    Removes all chunks belonging to a specific document - useful if
    a document is deleted or needs re-processing.
    """
    collection = get_collection()
    collection.delete(where={"document_id": document_id})