import chromadb
from chromadb.config import Settings
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.app.db.models import Document, DocumentChunk, DocumentStatus
from src.app.services.azure_openai_service import get_embedding, get_embeddings

CHROMA_PATH = "chroma_store"
COLLECTION_NAME = "claimiq_documents"


def get_chroma_client():
    return chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False),
    )


def get_or_create_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(name=COLLECTION_NAME)


def reset_collection():
    client = get_chroma_client()
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)

    return client.get_or_create_collection(name=COLLECTION_NAME)


def rebuild_chroma_index(db: Session) -> dict:
    collection = reset_collection()

    query = (
        select(DocumentChunk, Document)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(Document.status == DocumentStatus.ACTIVE)
        .order_by(Document.id, DocumentChunk.chunk_index)
    )

    rows = db.execute(query).all()

    if not rows:
        raise ValueError("No active document chunks found for indexing")

    documents = []
    embeddings_input = []
    metadatas = []
    ids = []

    for chunk, document in rows:
        chunk_id = f"doc-{document.id}-chunk-{chunk.id}"
        documents.append(chunk.chunk_text)
        embeddings_input.append(chunk.chunk_text)
        metadatas.append(
            {
                "document_id": document.id,
                "document_title": document.title,
                "filename": document.filename,
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "section_ref": chunk.section_ref or f"chunk-{chunk.chunk_index + 1}",
                "document_status": document.status.value,
            }
        )
        ids.append(chunk_id)

    embeddings = get_embeddings(embeddings_input)

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return {
        "indexed_chunks": len(ids),
        "collection_name": COLLECTION_NAME,
    }


def search_similar_chunks(question: str, top_k: int = 3) -> list[dict]:
    collection = get_or_create_collection()

    query_embedding = get_embedding(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    output = []
    for doc_text, metadata, distance in zip(documents, metadatas, distances):
        output.append(
            {
                "chunk_text": doc_text,
                "metadata": metadata,
                "distance": distance,
            }
        )

    return output