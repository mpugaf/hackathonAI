import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewHumanRequest(BaseModel):
    feedback: str = Field(min_length=1)
    decision: str = Field(pattern="^(aprobado|rechazado)$")


class RejectRequest(BaseModel):
    feedback: str = Field(min_length=1)


class ReviewOut(BaseModel):
    id: uuid.UUID
    requirement_version_id: uuid.UUID
    reviewer_id: uuid.UUID | None
    reviewer_type: str
    feedback: str
    ai_score: int | None
    decision: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
