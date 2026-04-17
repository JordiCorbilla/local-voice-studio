from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError, NotFoundError
from app.models.profile import Profile
from app.models.reference_clip import ReferenceClip
from app.repositories.clip_repository import ClipRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileCreate, ProfileUpdate
from app.services.audio_service import AudioService
from app.utils.files import compute_profile_fingerprint, safe_unlink
from app.utils.json import dumps, loads


class ProfileService:
    def __init__(self, settings: Settings, audio_service: AudioService) -> None:
        self.settings = settings
        self.audio_service = audio_service
        self.profiles = ProfileRepository()
        self.clips = ClipRepository()

    def list_profiles(self, session: Session) -> list[Profile]:
        return self.profiles.list(session)

    def get_profile(self, session: Session, profile_id: str) -> Profile:
        profile = self.profiles.get(session, profile_id)
        if not profile:
            raise NotFoundError("Profile not found.")
        return profile

    def create_profile(self, session: Session, payload: ProfileCreate) -> Profile:
        profile = Profile(
            id=str(uuid4()),
            display_name=payload.display_name.strip(),
            notes=payload.notes,
            language_preference=payload.language_preference,
            tags_json=dumps(payload.tags),
            avatar_color=payload.avatar_color,
            synthesis_defaults_json=payload.synthesis_defaults.model_dump_json(),
        )
        self.profiles.create(session, profile)
        session.commit()
        session.refresh(profile)
        return self.get_profile(session, profile.id)

    def update_profile(self, session: Session, profile_id: str, payload: ProfileUpdate) -> Profile:
        profile = self.get_profile(session, profile_id)
        updates = payload.model_dump(exclude_unset=True)
        if "display_name" in updates and updates["display_name"] is not None:
            profile.display_name = updates["display_name"].strip()
        if "notes" in updates:
            profile.notes = updates["notes"] or ""
        if "language_preference" in updates and updates["language_preference"] is not None:
            profile.language_preference = updates["language_preference"]
        if "tags" in updates and updates["tags"] is not None:
            profile.tags_json = dumps(updates["tags"])
        if "avatar_color" in updates and updates["avatar_color"] is not None:
            profile.avatar_color = updates["avatar_color"]
        if "synthesis_defaults" in updates and updates["synthesis_defaults"] is not None:
            profile.synthesis_defaults_json = updates["synthesis_defaults"].model_dump_json()

        session.commit()
        session.refresh(profile)
        return self.get_profile(session, profile_id)

    def delete_profile(self, session: Session, profile_id: str) -> None:
        profile = self.get_profile(session, profile_id)
        clip_paths = []
        generation_paths = []
        for clip in profile.clips:
            clip_paths.extend([Path(clip.original_path), Path(clip.normalized_path)])
        for generation in profile.generations:
            if generation.output_path:
                generation_paths.append(Path(generation.output_path))
        cache_path = Path(profile.conditioning_artifact_path) if profile.conditioning_artifact_path else None

        self.profiles.delete(session, profile)
        session.commit()

        self.audio_service.remove_clip_files(clip_paths)
        for generation_path in generation_paths:
            self.audio_service.remove_generation_file(generation_path)
        safe_unlink(cache_path)

    def list_clips(self, session: Session, profile_id: str) -> list[ReferenceClip]:
        self.get_profile(session, profile_id)
        return self.clips.list_for_profile(session, profile_id)

    def add_clip(
        self,
        session: Session,
        *,
        profile_id: str,
        filename: str,
        content_type: str,
        payload: bytes,
    ) -> ReferenceClip:
        profile = self.get_profile(session, profile_id)
        stored = self.audio_service.store_reference_audio(
            profile_id=profile_id,
            filename=filename,
            content_type=content_type,
            payload=payload,
        )

        existing_clips = self.clips.list_for_profile(session, profile_id)
        clip = ReferenceClip(
            id=stored.clip_id,
            profile_id=profile_id,
            original_path=str(stored.original_path),
            normalized_path=str(stored.normalized_path),
            original_filename=stored.original_filename,
            mime_type=stored.mime_type,
            duration_seconds=stored.metadata.duration_seconds,
            sample_rate=stored.metadata.sample_rate,
            channels=stored.metadata.channels,
            is_primary=not existing_clips,
        )
        self.clips.create(session, clip)
        self._invalidate_conditioning(profile)
        session.commit()
        session.refresh(clip)
        return clip

    def delete_clip(self, session: Session, profile_id: str, clip_id: str) -> None:
        profile = self.get_profile(session, profile_id)
        clip = self.clips.get(session, clip_id)
        if not clip or clip.profile_id != profile_id:
            raise NotFoundError("Reference clip not found.")

        clip_paths = [Path(clip.original_path), Path(clip.normalized_path)]
        was_primary = clip.is_primary
        self.clips.delete(session, clip)
        session.flush()

        if was_primary:
            remaining = self.clips.list_for_profile(session, profile_id)
            if remaining:
                remaining[0].is_primary = True

        self._invalidate_conditioning(profile)
        session.commit()
        self.audio_service.remove_clip_files(clip_paths)

    def set_primary_clip(self, session: Session, profile_id: str, clip_id: str) -> Profile:
        profile = self.get_profile(session, profile_id)
        clips = self.clips.list_for_profile(session, profile_id)
        if not any(clip.id == clip_id for clip in clips):
            raise NotFoundError("Reference clip not found.")
        for clip in clips:
            clip.is_primary = clip.id == clip_id
        self._invalidate_conditioning(profile)
        session.commit()
        return self.get_profile(session, profile_id)

    def normalized_clip_paths(self, profile: Profile) -> list[Path]:
        return [Path(clip.normalized_path) for clip in sorted(profile.clips, key=lambda item: item.created_at)]

    def primary_clip_path(self, profile: Profile) -> Path:
        primary = next((clip for clip in profile.clips if clip.is_primary), None)
        if primary:
            return Path(primary.normalized_path)
        if not profile.clips:
            raise AppError("Profile has no reference clips.", 400, "missing_reference_audio")
        return Path(profile.clips[0].normalized_path)

    def clip_fingerprint(self, profile: Profile) -> str | None:
        paths = self.normalized_clip_paths(profile)
        if not paths:
            return None
        return compute_profile_fingerprint(paths)

    def profile_tags(self, profile: Profile) -> list[str]:
        return loads(profile.tags_json, [])

    def profile_defaults(self, profile: Profile) -> dict:
        return loads(profile.synthesis_defaults_json, {})

    def _invalidate_conditioning(self, profile: Profile) -> None:
        if profile.conditioning_artifact_path:
            safe_unlink(Path(profile.conditioning_artifact_path))
        profile.conditioning_artifact_path = None
        profile.conditioning_fingerprint = None
