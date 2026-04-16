"""Resume model."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=False, index=True
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    target_jd: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    jd_keywords: Mapped[str] = mapped_column(Text, default="[]")
    template_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # JSON content
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    session: Mapped["Session"] = relationship("Session", back_populates="resumes")
    sections: Mapped[list["ResumeSection"]] = relationship(
        "ResumeSection", back_populates="resume", cascade="all, delete-orphan"
    )


class ResumeSection(Base):
    __tablename__ = "resume_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    resume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("resumes.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # summary | experience | projects | skills | education
    visible: Mapped[bool] = mapped_column(default=True)
    display_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    config: Mapped[str] = mapped_column(Text, default="{}")  # JSON config

    resume: Mapped["Resume"] = relationship("Resume", back_populates="sections")


from models.session import Session
