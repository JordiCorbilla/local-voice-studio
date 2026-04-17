from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    language_preference: Mapped[str] = mapped_column(String(32), default="en", nullable=False)
    tags_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    avatar_color: Mapped[str] = mapped_column(String(32), default="#7dd3fc", nullable=False)
    synthesis_defaults_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    conditioning_artifact_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    conditioning_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)

    clips = relationship(
        "ReferenceClip",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="ReferenceClip.created_at.desc()",
    )
    generations = relationship(
        "GenerationRecord",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="GenerationRecord.created_at.desc()",
    )
