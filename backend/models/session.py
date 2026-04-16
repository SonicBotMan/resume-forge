"""Session model."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), default="default", index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="upload"
    )  # upload | analyzing | editing | exporting | done
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    files: Mapped[list["File"]] = relationship(
        "File", back_populates="session", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="session", cascade="all, delete-orphan"
    )
    skills: Mapped[list["Skill"]] = relationship(
        "Skill", back_populates="session", cascade="all, delete-orphan"
    )
    achievements: Mapped[list["Achievement"]] = relationship(
        "Achievement", back_populates="session", cascade="all, delete-orphan"
    )
    resumes: Mapped[list["Resume"]] = relationship(
        "Resume", back_populates="session", cascade="all, delete-orphan"
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="sessions")


from models.file import File
from models.project import Project
from models.skill import Skill
from models.achievement import Achievement
from models.resume import Resume
