"""Database setup and models."""

import json
from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from config import settings


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


# Synchronous engine for migrations/setup
_sync_url = settings.database_url.replace("sqlite+aiosqlite", "sqlite")
sync_engine = create_engine(
    _sync_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Asynchronous engine for API
async_engine = create_async_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# PRAGMA settings for SQLite performance
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


event.listens_for(sync_engine, "connect")(_set_sqlite_pragmas)
event.listens_for(async_engine.sync_engine, "connect")(_set_sqlite_pragmas)

# Session factories
SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def init_db():
    """Initialize database tables (sync version for startup)."""
    Base.metadata.create_all(bind=sync_engine)
    ensure_indexes(sync_engine)


def ensure_indexes(engine):
    """Create indexes if they don't exist (for existing databases)."""
    from sqlalchemy import text, inspect

    with engine.connect() as conn:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        for table_name, column_name in [
            ("files", "session_id"),
            ("files", "parse_status"),
            ("chunks", "session_id"),
            ("chunks", "file_id"),
            ("projects", "session_id"),
            ("skills", "session_id"),
            ("achievements", "session_id"),
            ("achievements", "project_id"),
            ("resumes", "session_id"),
            ("materials", "user_id"),
            ("materials", "analysis_status"),
            ("material_analyses", "material_id"),
            ("material_analyses", "user_id"),
            ("job_descriptions", "user_id"),
            ("base_resumes", "user_id"),
            ("targeted_resumes", "user_id"),
            ("targeted_resumes", "jd_id"),
            ("review_sessions", "user_id"),
            ("review_sessions", "resume_id"),
        ]:
            if table_name not in existing_tables:
                continue
            index_name = f"ix_{table_name}_{column_name}"
            existing = [idx["name"] for idx in inspector.get_indexes(table_name)]
            if index_name not in existing:
                conn.execute(
                    text(
                        f"CREATE INDEX {index_name} ON {table_name} ({column_name})"
                    )
                )
        for table_name, index_name, columns in [
            ("materials", "idx_material_user_status", ["user_id", "analysis_status"]),
            ("materials", "idx_material_user_created", ["user_id", "created_at"]),
        ]:
            if table_name not in existing_tables:
                continue
            existing = [idx["name"] for idx in inspector.get_indexes(table_name)]
            if index_name not in existing:
                conn.execute(
                    text(
                        f"CREATE INDEX {index_name} ON {table_name} ({', '.join(columns)})"
                    )
                )
        conn.commit()


# JSON field helpers
def json_field(default=None):
    """Return default value for JSON column."""
    return default or []


# Import models after Base is defined
from models.session import Session
from models.file import File
from models.chunk import Chunk
from models.company import Company
from models.project import Project
from models.skill import Skill
from models.achievement import Achievement
from models.resume import Resume, ResumeSection
from models.activation import ActivationCode, DeviceActivation
from models.user import User
from models.material import Material
from models.material_analysis import MaterialAnalysis
from models.job_description import JobDescription
from models.base_resume import BaseResume
from models.targeted_resume import TargetedResume
from models.review_session import ReviewSession

__all__ = [
    "Base",
    "Session",
    "File",
    "Chunk",
    "Company",
    "Project",
    "Skill",
    "Achievement",
    "Resume",
    "ResumeSection",
    "ActivationCode",
    "DeviceActivation",
    "User",
    "Material",
    "MaterialAnalysis",
    "JobDescription",
    "BaseResume",
    "TargetedResume",
    "ReviewSession",
    "get_db",
    "init_db",
    "sync_engine",
    "async_engine",
]
