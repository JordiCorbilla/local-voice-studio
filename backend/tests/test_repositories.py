from __future__ import annotations

from uuid import uuid4

from app.models.generation import GenerationRecord
from app.models.profile import Profile
from app.models.reference_clip import ReferenceClip
from app.repositories.generation_repository import GenerationRepository
from app.repositories.profile_repository import ProfileRepository


def test_profile_and_generation_repositories(container):
    profiles = ProfileRepository()
    generations = GenerationRepository()

    with container.session_factory() as session:
        profile = Profile(
            id=str(uuid4()),
            display_name="Narrator",
            notes="",
            language_preference="en",
            tags_json="[]",
            avatar_color="#ffffff",
            synthesis_defaults_json="{}",
        )
        profiles.create(session, profile)

        clip = ReferenceClip(
            id=str(uuid4()),
            profile_id=profile.id,
            original_path="orig.wav",
            normalized_path="norm.wav",
            original_filename="orig.wav",
            mime_type="audio/wav",
            duration_seconds=3.0,
            sample_rate=24000,
            channels=1,
            is_primary=True,
        )
        session.add(clip)
        generation = GenerationRecord(
            id=str(uuid4()),
            profile_id=profile.id,
            input_text="Hello test",
            language="en",
            parameters_json="{}",
            status="queued",
        )
        generations.create(session, generation)
        session.commit()

        assert len(profiles.list(session)) == 1
        assert generations.get(session, generation.id) is not None
        assert len(generations.list(session, profile.id)) == 1
