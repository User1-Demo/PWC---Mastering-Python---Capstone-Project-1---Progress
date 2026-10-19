"""
retriever.py (ai_rag module)

Purpose: Given a user's question, find the most relevant chunks,
filter out deactivated documents (BR-006), and apply a confidence
threshold so we NEVER pass weak matches to the LLM (BR-005).
"""

from src.ai_rag.embeddings import embed_text
from src.ai_rag.vector_store import query_similar_chunks
from src.documents.models import Document
from sqlalchemy.orm import Session

# Chroma returns "distance" (lower = more similar) for the default
# embedding space. We convert to a 0-1 "similarity" score for easier
# reasoning, and reject anything below this threshold.
CONFIDENCE_THRESHOLD = 0.20
LOW_CONFIDENCE_THRESHOLD = 0.30
TOP_K = 4


def distance_to_similarity(distance: float) -> float:
    """
    Chroma's default distance metric is L2 (Euclidean) by default,
    but for normalized embeddings (like OpenAI's), cosine distance
    behaves predictably: similarity = 1 - distance works well enough
    as an approximation for our confidence gating purposes.
    """
    return max(0.0, 1.0 - distance)


def retrieve_relevant_chunks(db: Session, question: str) -> dict:
    """
    Returns a dict:
    {
        "chunks": [ {text, document_id, document_title, chunk_index, similarity}, ... ],
        "confidence": "ok" | "low" | "no_match"
    }

    Only chunks from ACTIVE documents are returned (BR-006).
    """
    query_vector = embed_text(question)

    # Over-fetch slightly, since we'll filter some out due to deactivated docs
    raw_results = query_similar_chunks(query_vector, top_k=TOP_K * 2)

    if not raw_results["ids"][0]:
        return {"chunks": [], "confidence": "no_match"}

    candidate_chunks = []
    for i in range(len(raw_results["ids"][0])):
        document_id = raw_results["metadatas"][0][i]["document_id"]
        distance = raw_results["distances"][0][i]
        similarity = distance_to_similarity(distance)

        candidate_chunks.append({
            "text": raw_results["documents"][0][i],
            "document_id": document_id,
            "document_title": raw_results["metadatas"][0][i]["document_title"],
            "chunk_index": raw_results["metadatas"][0][i]["chunk_index"],
            "similarity": similarity,
        })

    # BR-006: filter out chunks whose parent document is deactivated
    active_document_ids = {
        str(doc.id) for doc in db.query(Document.id).filter(Document.status == "active").all()
    }
    filtered_chunks = [
        c for c in candidate_chunks if c["document_id"] in active_document_ids
    ]

    # Keep only the top TOP_K after filtering
    filtered_chunks = sorted(filtered_chunks, key=lambda c: c["similarity"], reverse=True)[:TOP_K]

    if not filtered_chunks:
        return {"chunks": [], "confidence": "no_match"}

    best_similarity = filtered_chunks[0]["similarity"]

    if best_similarity < CONFIDENCE_THRESHOLD:
        confidence = "no_match"
    elif best_similarity < LOW_CONFIDENCE_THRESHOLD:
        confidence = "low"
    elif best_similarity < CONFIDENCE_THRESHOLD + 0.1:
        confidence = "low"
    else:
        confidence = "ok"

    return {"chunks": filtered_chunks, "confidence": confidence}