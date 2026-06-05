import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    description: str | None = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    created_by: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
