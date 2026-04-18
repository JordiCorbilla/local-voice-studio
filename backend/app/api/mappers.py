from __future__ import annotations

from pathlib import Path

from app.models.generation import GenerationRecord as GenerationRecordModel
from app.models.profile import Profile
from app.models.reference_clip import ReferenceClip as ReferenceClipModel
from app.schemas.generation import GenerationRecord
from app.schemas.profile import ProfileDetail, ProfileSummary, ReferenceClip
from app.utils.json import loads


def _reference_relative_path(path: Path) -> str:
    parts = list(path.parts)
    if "profiles" in parts:
        index = parts.index("profiles")
        return Path(*parts[index + 1 :]).as_posix()
    return path.name


def map_clip(clip: ReferenceClipModel) -> ReferenceClip:
    normalized_path = Path(clip.normalized_path)
    return ReferenceClip(
        id=clip.id,
        profile_id=clip.profile_id,
        original_filename=clip.original_filename,
        mime_type=clip.mime_type,
        duration_seconds=clip.duration_seconds,
        sample_rate=clip.sample_rate,
        channels=clip.channels,
        is_primary=clip.is_primary,
        reference_text=clip.reference_text,
        transcript_source=clip.transcript_source,
        created_at=clip.created_at,
        original_file=clip.original_path,
        normalized_file=clip.normalized_path,
        audio_url=f"/api/files/reference/{_reference_relative_path(normalized_path)}",
    )


def map_generation(record: GenerationRecordModel) -> GenerationRecord:
    output_url = None
    output_file = None
    if record.output_path:
        output_file = Path(record.output_path).name
        output_url = f"/api/files/generated/{output_file}"
    return GenerationRecord(
        id=record.id,
        profile_id=record.profile_id,
        input_text=record.input_text,
        language=record.language,
        engine_name=record.engine_name,
        delivery_instructions=record.delivery_instructions,
        seed=record.seed,
        parameters=loads(record.parameters_json, {}),
        output_file=output_file,
        output_url=output_url,
        duration_seconds=record.duration_seconds,
        status=record.status,
        error_message=record.error_message,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def map_profile_summary(profile: Profile) -> ProfileSummary:
    primary = next((clip for clip in profile.clips if clip.is_primary), None)
    return ProfileSummary(
        id=profile.id,
        display_name=profile.display_name,
        notes=profile.notes,
        language_preference=profile.language_preference,
        tags=loads(profile.tags_json, []),
        avatar_color=profile.avatar_color,
        synthesis_defaults=loads(profile.synthesis_defaults_json, {}),
        clip_count=len(profile.clips),
        primary_clip_id=primary.id if primary else None,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def map_profile_detail(profile: Profile) -> ProfileDetail:
    return ProfileDetail(
        **map_profile_summary(profile).model_dump(),
        clips=[map_clip(clip) for clip in sorted(profile.clips, key=lambda item: item.created_at, reverse=True)],
        recent_generations=[map_generation(record) for record in list(profile.generations)[:10]],
    )
