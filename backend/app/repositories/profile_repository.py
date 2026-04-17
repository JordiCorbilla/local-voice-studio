from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.profile import Profile


class ProfileRepository:
    def list(self, session: Session) -> list[Profile]:
        stmt = (
            select(Profile)
            .options(selectinload(Profile.clips), selectinload(Profile.generations))
            .order_by(Profile.updated_at.desc())
            .execution_options(populate_existing=True)
        )
        return list(session.scalars(stmt).all())

    def get(self, session: Session, profile_id: str) -> Profile | None:
        stmt = (
            select(Profile)
            .where(Profile.id == profile_id)
            .options(selectinload(Profile.clips), selectinload(Profile.generations))
            .execution_options(populate_existing=True)
        )
        return session.scalars(stmt).first()

    def create(self, session: Session, profile: Profile) -> Profile:
        session.add(profile)
        session.flush()
        return profile

    def delete(self, session: Session, profile: Profile) -> None:
        session.delete(profile)
