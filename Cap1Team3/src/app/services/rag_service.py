from sqlalchemy.orm import Session

from src.app.db.models import ChatQueryLog, User
from src.app.schemas.ai import AIQueryResponse
from src.app.services.azure_openai_service import generate_answer
from src.app.services.chroma_service import search_similar_chunks


def build_prompt(question: str, retrieved_chunks: list[dict]) -> tuple[str, list[str]]:
    context_parts = []
    sources = []

    for item in retrieved_chunks:
        metadata = item["metadata"]
        source_ref = (
            f"{metadata['document_title']} | {metadata['section_ref']}"
        )
        sources.append(source_ref)

        context_parts.append(
            f"Source: {source_ref}\n"
            f"Content: {item['chunk_text']}"
        )

    context_text = "\n\n".join(context_parts)

    prompt = (
        "Use only the context below to answer the question.\n"
        "If the answer is not found in the context, say exactly: "
        "'No relevant information was found in the approved documents.'\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question:\n{question}\n\n"
        "Return a concise answer grounded only in the context."
    )

    return prompt, sources


def answer_question(
    db: Session,
    *,
    current_user: User,
    question: str,
    top_k: int = 3,
) -> AIQueryResponse:
    retrieved_chunks = search_similar_chunks(question, top_k=top_k)

    if not retrieved_chunks:
        answer = "No relevant information was found in the approved documents."
        log = ChatQueryLog(
            user_id=current_user.id,
            question=question,
            answer=answer,
            source_reference=None,
            confidence_flag="no_match",
            tokens_used=None,
        )
        db.add(log)
        db.commit()

        return AIQueryResponse(
            answer=answer,
            sources=[],
            confidence_flag="no_match",
        )

    prompt, sources = build_prompt(question, retrieved_chunks)
    answer, tokens_used = generate_answer(prompt)

    confidence_flag = None
    if "No relevant information was found in the approved documents." in answer:
        confidence_flag = "low_confidence"

    source_reference = "; ".join(sources)

    log = ChatQueryLog(
        user_id=current_user.id,
        question=question,
        answer=answer,
        source_reference=source_reference,
        confidence_flag=confidence_flag,
        tokens_used=tokens_used,
    )
    db.add(log)
    db.commit()

    return AIQueryResponse(
        answer=answer,
        sources=sources,
        confidence_flag=confidence_flag,
    )