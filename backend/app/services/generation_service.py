from __future__ import annotations

from concurrent.futures import Executor
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.core.errors import AppError, ConflictError, NotFoundError
from app.models.generation import GenerationRecord
from app.repositories.generation_repository import GenerationRepository
from app.schemas.generation import GenerationRequest
from app.services.audio_service import AudioService
from app.services.profile_service import ProfileService
from app.services.tts.base import PreparedProfile, SynthesisPayload, TtsEngine
from app.utils.json import dumps, loads


class GenerationService:
    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: sessionmaker,
        tts_engine: TtsEngine,
        audio_service: AudioService,
        executor: Executor,
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.tts_engine = tts_engine
        self.audio_service = audio_service
        self.executor = executor
        self.generations = GenerationRepository()
        self.profile_service = ProfileService(settings, audio_service)

    def list_generations(self, session, profile_id: str | None = None) -> list[GenerationRecord]:
        return self.generations.list(session, profile_id)

    def get_generation(self, session, generation_id: str) -> GenerationRecord:
        generation = self.generations.get(session, generation_id)
        if not generation:
            raise NotFoundError("Generation not found.")
        return generation

    def enqueue_generation(self, session, payload: GenerationRequest) -> GenerationRecord:
        if not payload.input_text.strip():
            raise AppError("Text input cannot be empty.", 400, "empty_text")

        profile = self.profile_service.get_profile(session, payload.profile_id)
        if not profile.clips:
            raise AppError("A profile must have at least one reference clip before synthesis.", 400, "missing_reference_audio")

        parameters = self.profile_service.profile_defaults(profile)
        if payload.parameters is not None:
            parameters.update(payload.parameters.model_dump())

        record = GenerationRecord(
            id=str(uuid4()),
            profile_id=payload.profile_id,
            input_text=payload.input_text.strip(),
            language=payload.language or profile.language_preference,
            engine_name=self.tts_engine.name,
            delivery_instructions=(payload.delivery_instructions or "").strip() or None,
            seed=payload.seed,
            parameters_json=dumps(parameters),
            status="queued",
        )
        if self.tts_engine.name == "qwen3-tts" and not self.profile_service.primary_clip_reference_text(profile):
            raise AppError(
                "Qwen3 voice cloning requires a transcript for the selected primary reference clip.",
                400,
                "missing_reference_transcript",
            )
        self.generations.create(session, record)
        session.commit()
        session.refresh(record)
        self.executor.submit(self._run_generation_job, record.id)
        return record

    def delete_generation(self, session, generation_id: str) -> None:
        generation = self.get_generation(session, generation_id)
        if generation.status in {"queued", "running"}:
            raise ConflictError("Cannot delete a generation while it is still running.")
        output_path = Path(generation.output_path) if generation.output_path else None
        self.generations.delete(session, generation)
        session.commit()
        self.audio_service.remove_generation_file(output_path)

    def _run_generation_job(self, generation_id: str) -> None:
        with self.session_factory() as session:
            record = self.generations.get(session, generation_id)
            if not record:
                return
            try:
                record.status = "running"
                session.commit()

                profile = self.profile_service.get_profile(session, record.profile_id)
                fingerprint = self.profile_service.clip_fingerprint(profile)
                if not fingerprint:
                    raise AppError("Profile has no valid normalized clips.", 400, "missing_reference_audio")

                prepared = PreparedProfile(
                    profile_id=profile.id,
                    language=profile.language_preference,
                    reference_paths=self.profile_service.conditioning_clip_paths(profile),
                    primary_reference_path=self.profile_service.primary_clip_path(profile),
                    primary_reference_text=self.profile_service.primary_clip_reference_text(profile),
                    conditioning_artifact_path=Path(profile.conditioning_artifact_path) if profile.conditioning_artifact_path else None,
                    conditioning_fingerprint=fingerprint,
                )
                prepared = self.tts_engine.prepare_profile(prepared)

                if prepared.conditioning_artifact_path:
                    profile.conditioning_artifact_path = str(prepared.conditioning_artifact_path)
                    profile.conditioning_fingerprint = prepared.conditioning_fingerprint
                    session.commit()

                output_path = self.settings.generated_dir / f"{record.id}.wav"
                synthesis_payload = SynthesisPayload(
                    text=record.input_text,
                    language=record.language,
                    delivery_instructions=record.delivery_instructions,
                    seed=record.seed,
                    parameters=loads(record.parameters_json, {}),
                )
                self.tts_engine.synthesize(prepared, synthesis_payload, output_path)

                record.output_path = str(output_path)
                record.duration_seconds = self.audio_service.probe_output_duration(output_path)
                record.status = "completed"
                record.error_message = None
            except AppError as exc:
                record.status = "failed"
                record.error_message = exc.message
            except Exception as exc:
                record.status = "failed"
                record.error_message = str(exc)
            finally:
                session.commit()
