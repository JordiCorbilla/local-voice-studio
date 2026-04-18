from __future__ import annotations

from pathlib import Path

from app.models.profile import Profile
from app.schemas.profile import ProfileCreate
from app.services.audio_service import AudioMetadata, StoredClip
from app.services.profile_service import ProfileService


def test_profile_service_invalidates_conditioning_and_primary_clip(settings, tmp_path, monkeypatch):
    settings.ensure_directories()
    service = ProfileService(settings, audio_service=None)  # type: ignore[arg-type]
    created = []

    def fake_store_reference_audio(*, profile_id: str, filename: str, content_type: str, payload: bytes):
        clip_id = f"clip-{len(created) + 1}"
        clip_dir = settings.profiles_dir / profile_id / "clips" / clip_id
        clip_dir.mkdir(parents=True, exist_ok=True)
        original_path = clip_dir / "original.wav"
        normalized_path = clip_dir / "normalized.wav"
        original_path.write_bytes(b"orig")
        normalized_path.write_bytes(b"norm")
        created.append(clip_id)
        return StoredClip(
            clip_id=clip_id,
            original_path=original_path,
            normalized_path=normalized_path,
            original_filename=filename,
            mime_type=content_type,
            metadata=AudioMetadata(duration_seconds=3.1, sample_rate=24000, channels=1),
        )

    service.audio_service = type("AudioStub", (), {"store_reference_audio": staticmethod(fake_store_reference_audio), "remove_clip_files": staticmethod(lambda paths: None), "remove_generation_file": staticmethod(lambda path: None)})()  # type: ignore[assignment]

    container_db = settings.database_url
    from app.db.base import Base
    from app.db.session import create_engine, create_session_factory

    engine = create_engine(container_db)
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        profile = service.create_profile(
            session,
            ProfileCreate(display_name="Voice", notes="", language_preference="en", tags=[], avatar_color="#fff"),
        )
        profile.conditioning_artifact_path = str(tmp_path / "conditioning.pt")
        Path(profile.conditioning_artifact_path).write_text("cache", encoding="utf-8")
        session.commit()

        first = service.add_clip(session, profile_id=profile.id, filename="a.wav", content_type="audio/wav", payload=b"1")
        second = service.add_clip(session, profile_id=profile.id, filename="b.wav", content_type="audio/wav", payload=b"1")

        assert first.is_primary is True
        assert second.is_primary is False

        profile = service.set_primary_clip(session, profile.id, second.id)
        assert any(clip.id == second.id and clip.is_primary for clip in profile.clips)
        assert profile.conditioning_artifact_path is None
        assert service.conditioning_clip_paths(profile) == [Path(second.normalized_path)]
