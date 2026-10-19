from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClaimNoteCreate(BaseModel):
    note_text: str = Field(min_length=1, max_length=5000)


class ClaimNoteResponse(BaseModel):
    id: int
    claim_id: int
    author_id: int
    note_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)