import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas.review import ReviewOut


class VersionOut(BaseModel):
    id: uuid.UUID
    requirement_id: uuid.UUID
    version_number: int
    generated_spec: str
    model_used: str
    prompt_used: str
    feedback_context: str | None
    created_at: datetime
    reviews: list[ReviewOut] = []

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
