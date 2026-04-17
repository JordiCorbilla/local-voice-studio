from __future__ import annotations

from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.orm import sessionmaker


def create_engine(database_url: str):
    return sqlalchemy_create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )


def create_session_factory(engine) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
