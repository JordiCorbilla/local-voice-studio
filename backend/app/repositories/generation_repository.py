from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.generation import GenerationRecord


class GenerationRepository:
    def list(self, session: Session, profile_id: str | None = None) -> list[GenerationRecord]:
        stmt = select(GenerationRecord).order_by(GenerationRecord.created_at.desc())
        if profile_id:
            stmt = stmt.where(GenerationRecord.profile_id == profile_id)
        return list(session.scalars(stmt).all())

    def get(self, session: Session, generation_id: str) -> GenerationRecord | None:
        return session.get(GenerationRecord, generation_id)

    def create(self, session: Session, record: GenerationRecord) -> GenerationRecord:
        session.add(record)
        session.flush()
        return record

    def delete(self, session: Session, record: GenerationRecord) -> None:
        session.delete(record)
