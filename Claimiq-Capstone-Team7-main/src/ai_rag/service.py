"""
service.py (ai_rag module)

Purpose: Orchestrates the full query flow: retrieve -> confidence
gate -> generate -> log to ChatQueryLog (FR-013) -> return.
"""

from sqlalchemy.orm import Session

from src.ai_rag.retriever import retrieve_relevant_chunks
from src.ai_rag.prompt_builder import build_messages
from src.ai_rag.llm_client import generate_answer
from src.ai_rag.models import ChatQueryLog
from src.users.models import User


def answer_question(db: Session, question: str, current_user: User) -> dict:
    retrieval_result = retrieve_relevant_chunks(db, question)
    confidence = retrieval_result["confidence"]
    chunks = retrieval_result["chunks"]

    if confidence == "no_match":
        answer_text = "No relevant information was found in the approved documents for this question."
        source = None
        prompt_tokens = 0
        completion_tokens = 0
    else:
        messages = build_messages(question, chunks)
        llm_result = generate_answer(messages)
        answer_text = llm_result["answer"]
        prompt_tokens = llm_result["prompt_tokens"]
        completion_tokens = llm_result["completion_tokens"]
        # Cite the top (most similar) chunk's source document
        source = f"{chunks[0]['document_title']}, Chunk {chunks[0]['chunk_index']}"

    # FR-013: log every AI query - question, sources used, response, confidence
    chunk_ids = [f"{c['document_id']}_{c['chunk_index']}" for c in chunks]

    log_entry = ChatQueryLog(
        user_id=current_user.id,
        question=question,
        retrieved_chunk_ids=chunk_ids,
        response_text=answer_text,
        source_citation=source,
        confidence_flag=confidence,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    db.add(log_entry)
    db.commit()

    return {
        "answer": answer_text,
        "source": source,
        "confidence": confidence,
    }