"""
document_processor.py (ai_rag module)

Purpose: Orchestrates the full ingestion pipeline for ONE document:
extract text -> chunk -> embed -> store in ChromaDB.

This gets called right after a document is uploaded (we'll wire
this into documents/service.py next).
"""

from src.ai_rag.text_extraction import extract_text
from src.ai_rag.chunking import chunk_text, count_tokens
from src.ai_rag.embeddings import embed_batch
from src.ai_rag.vector_store import add_chunks


def process_document(document_id: str, title: str, file_path: str) -> int:
    """
    Returns the number of chunks created.
    """
    raw_text = extract_text(file_path)

    if not raw_text.strip():
        return 0  # empty/unreadable document - nothing to index

    chunks = chunk_text(raw_text)
    vectors = embed_batch(chunks)

    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "document_id": document_id,
            "document_title": title,
            "chunk_index": i,
            "token_count": count_tokens(chunk),
        }
        for i, chunk in enumerate(chunks)
    ]

    add_chunks(ids=ids, embeddings=vectors, documents=chunks, metadatas=metadatas)

    return len(chunks)