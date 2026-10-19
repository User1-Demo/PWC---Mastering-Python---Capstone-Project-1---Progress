from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from src.database import Base


class ChatQueryLog(Base):
    __tablename__ = "chat_query_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    retrieved_chunk_ids = Column(ARRAY(String), nullable=True)
    response_text = Column(Text, nullable=True)
    source_citation = Column(String(255), nullable=True)
    confidence_flag = Column(String(20), nullable=False)  # ok/low/no_match
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())