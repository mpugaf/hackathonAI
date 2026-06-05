import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class RequirementVersion(Base):
    __tablename__ = "requirement_versions"
    __table_args__ = (UniqueConstraint("requirement_id", "version_number", name="uq_req_version"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("requirements.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_spec: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_used: Mapped[str] = mapped_column(Text, nullable=False)
    feedback_context: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    requirement = relationship("Requirement", back_populates="versions")
    reviews = relationship("Review", back_populates="requirement_version", cascade="all, delete-orphan")
