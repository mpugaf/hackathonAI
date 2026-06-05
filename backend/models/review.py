import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (CheckConstraint("ai_score IS NULL OR (ai_score >= 0 AND ai_score <= 100)", name="ck_reviews_ai_score"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_version_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("requirement_versions.id"), nullable=False)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    reviewer_type: Mapped[str] = mapped_column(String(20), nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    ai_score: Mapped[int | None] = mapped_column(SmallInteger)
    decision: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    requirement_version = relationship("RequirementVersion", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")
