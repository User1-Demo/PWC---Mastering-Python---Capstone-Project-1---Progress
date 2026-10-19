from pydantic import BaseModel, Field


class AIQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class CitationResponse(BaseModel):
    document_id: int
    document_title: str
    page_number: int | None = None
    section_name: str | None = None


class AIQueryResponse(BaseModel):
    answer: str
    citations: list[CitationResponse] = Field(default_factory=list)