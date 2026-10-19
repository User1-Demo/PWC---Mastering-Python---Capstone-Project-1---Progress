"""
router.py (ai_rag module)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.users.models import User
from src.auth.dependencies import get_current_user
from src.ai_rag.schemas import AIQueryRequest, AIQueryResponse
from src.ai_rag import service

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.post("/query", response_model=AIQueryResponse)
def query_ai(
    payload: AIQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # any authenticated role can ask
):
    return service.answer_question(db, payload.question, current_user)