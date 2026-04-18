from __future__ import annotations

from sqlalchemy import inspect, text


def run_startup_migrations(engine) -> None:
    inspector = inspect(engine)

    if "reference_clips" in inspector.get_table_names():
        clip_columns = {column["name"] for column in inspector.get_columns("reference_clips")}
        _ensure_column(
            engine,
            table_name="reference_clips",
            existing_columns=clip_columns,
            column_name="reference_text",
            sql="ALTER TABLE reference_clips ADD COLUMN reference_text TEXT NOT NULL DEFAULT ''",
        )
        _ensure_column(
            engine,
            table_name="reference_clips",
            existing_columns=clip_columns,
            column_name="transcript_source",
            sql="ALTER TABLE reference_clips ADD COLUMN transcript_source VARCHAR(32)",
        )

    if "generation_records" in inspector.get_table_names():
        generation_columns = {column["name"] for column in inspector.get_columns("generation_records")}
        _ensure_column(
            engine,
            table_name="generation_records",
            existing_columns=generation_columns,
            column_name="engine_name",
            sql="ALTER TABLE generation_records ADD COLUMN engine_name VARCHAR(32) NOT NULL DEFAULT 'xtts'",
        )
        _ensure_column(
            engine,
            table_name="generation_records",
            existing_columns=generation_columns,
            column_name="delivery_instructions",
            sql="ALTER TABLE generation_records ADD COLUMN delivery_instructions TEXT",
        )
        _ensure_column(
            engine,
            table_name="generation_records",
            existing_columns=generation_columns,
            column_name="seed",
            sql="ALTER TABLE generation_records ADD COLUMN seed INTEGER",
        )


def _ensure_column(engine, *, table_name: str, existing_columns: set[str], column_name: str, sql: str) -> None:
    if column_name in existing_columns:
        return
    with engine.begin() as connection:
        connection.execute(text(sql))
    existing_columns.add(column_name)
