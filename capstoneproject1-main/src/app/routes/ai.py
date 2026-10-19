from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.app.core.security import get_current_user
from src.app.db.models import ChatQueryLog, User, UserRole
from src.app.db.session import get_db
from src.app.schemas.ai import AIQueryRequest, AIQueryResponse, ChatQueryLogResponse
from src.app.services.chroma_service import rebuild_chroma_index
from src.app.services.rag_service import answer_question

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/query",
    response_model=AIQueryResponse,
)
def query_ai(
    payload: AIQueryRequest,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    return answer_question(
        db,
        current_user=current_user,
        question=payload.question,
        top_k=payload.top_k,
    )


@router.post(
    "/reindex",
)
def reindex_documents(
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can rebuild the AI index",
        )

    result = rebuild_chroma_index(db)
    return {
        "message": "ChromaDB index rebuilt successfully",
        **result,
    }


@router.get(
    "/logs",
    response_model=list[ChatQueryLogResponse],
)
def list_ai_logs(
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view AI query logs",
        )

    logs = db.scalars(
        select(ChatQueryLog).order_by(ChatQueryLog.created_at.desc())
    ).all()

    return logs