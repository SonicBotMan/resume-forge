"""Project model."""

from typing import Optional
from sqlalchemy import String, Text, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=False, index=True
    )
    company_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("companies.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    situation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source_chunk_ids: Mapped[str] = mapped_column(Text, default="[]")
    source_file_ids: Mapped[str] = mapped_column(Text, default="[]")
    is_selected: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    session: Mapped["Session"] = relationship("Session", back_populates="projects")
    company: Mapped[Optional["Company"]] = relationship(
        "Company", back_populates="projects"
    )


from models.session import Session
from models.company import Company
