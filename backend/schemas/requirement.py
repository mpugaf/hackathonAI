import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.requirement_version import VersionOut
from schemas.review import ReviewOut


class RequirementCreate(BaseModel):
    project_id: uuid.UUID
    title: str = Field(min_length=5, max_length=300)
    raw_input: str = Field(min_length=20)


class RequirementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=300)
    raw_input: str | None = Field(default=None, min_length=20)


class RequirementOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    raw_input: str
    status: str
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    version_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class RequirementDetail(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    raw_input: str
    status: str
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    latest_version: VersionOut | None = None
    latest_ai_review: ReviewOut | None = None
    latest_human_review: ReviewOut | None = None

    model_config = ConfigDict(from_attributes=True)
