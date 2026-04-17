from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reference_clip import ReferenceClip


class ClipRepository:
    def list_for_profile(self, session: Session, profile_id: str) -> list[ReferenceClip]:
        stmt = (
            select(ReferenceClip)
            .where(ReferenceClip.profile_id == profile_id)
            .order_by(ReferenceClip.is_primary.desc(), ReferenceClip.created_at.desc())
        )
        return list(session.scalars(stmt).all())

    def get(self, session: Session, clip_id: str) -> ReferenceClip | None:
        return session.get(ReferenceClip, clip_id)

    def create(self, session: Session, clip: ReferenceClip) -> ReferenceClip:
        session.add(clip)
        session.flush()
        return clip

    def delete(self, session: Session, clip: ReferenceClip) -> None:
        session.delete(clip)
