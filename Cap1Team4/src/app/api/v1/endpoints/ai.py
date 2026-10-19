import threading
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_roles
from app.core.config import settings
from app.core.exceptions import RateLimitedError
from app.db.session import get_db
from app.models.audit import ChatQueryLog
from app.models.document import Document, DocumentChunk
from app.models.enums import DocumentStatus, UserRole
from app.models.user import User
from app.rag.retrieval import grounded_answer, rank_chunks
from app.schemas.ai import ChatQuery, ChatQueryOut, Citation
from app.utils.redaction import redact_pii

router = APIRouter(prefix="/ai", tags=["ai"])
authenticated = require_roles(
    UserRole.ADMIN,
    UserRole.CLAIMS_MANAGER,
    UserRole.CLAIMS_ADJUSTER,
    UserRole.SUPPORT_AGENT,
)
_requests: dict[str, deque[float]] = defaultdict(deque)
_rate_limit_lock = threading.Lock()


def _enforce_rate_limit(user_id: str) -> None:
    now = time.monotonic()
    cutoff = now - 60
    with _rate_limit_lock:
        requests = _requests[user_id]
        while requests and requests[0] <= cutoff:
            requests.popleft()
        if len(requests) >= settings.AI_RATE_LIMIT_PER_MINUTE:
            raise RateLimitedError()
        requests.append(now)


@router.post("/query", response_model=ChatQueryOut)
def query_documents(
    payload: ChatQuery,
    db: Session = Depends(get_db),
    user: User = Depends(authenticated),
) -> ChatQueryOut:
    started = time.monotonic()
    _enforce_rate_limit(str(user.id))
    query = select(DocumentChunk).join(Document).options(
        joinedload(DocumentChunk.document)
    ).where(
        Document.is_active.is_(True),
        Document.status == DocumentStatus.ACTIVE,
        DocumentChunk.is_active.is_(True),
    )
    if payload.policy_type is not None:
        query = query.where(
            (Document.applies_to.is_(None))
            | (Document.applies_to == payload.policy_type)
        )
    candidates = list(db.scalars(query))
    results = rank_chunks(
        payload.question,
        candidates,
        top_k=min(payload.top_k, settings.RAG_TOP_K),
    )
    citations = [
        Citation(
            document_id=chunk.document.id,
            document_title=chunk.document.title,
            chunk_id=chunk.id,
            section_heading=chunk.section_heading,
            page_number=chunk.page_number,
            score=round(score, 4),
        )
        for score, chunk in results
    ]
    no_match = not results
    answer = grounded_answer(results)
    safe_question = redact_pii(payload.question)
    prompt_tokens = len(safe_question.split()) + sum(
        chunk.token_count for _, chunk in results
    )
    completion_tokens = len(answer.split())
    confidence = max((score for score, _ in results), default=0.0)
    db.add(
        ChatQueryLog(
            user_id=user.id,
            question=safe_question,
            answer=redact_pii(answer),
            source_chunk_ids=[str(c.chunk_id) for c in citations],
            similarity_scores=[c.score for c in citations],
            top_k=min(payload.top_k, settings.RAG_TOP_K),
            confidence_score=confidence,
            is_no_match=no_match,
            flagged_for_review=no_match or confidence < 0.5,
            model_name="extractive-approved-document-search",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=int((time.monotonic() - started) * 1000),
            status="success",
        )
    )
    db.commit()
    return ChatQueryOut(answer=answer, citations=citations, no_match=no_match)
