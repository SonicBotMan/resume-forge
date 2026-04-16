"""Skill model."""

from typing import Optional
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # technical | methodology | tool
    source_chunk_ids: Mapped[str] = mapped_column(Text, default="[]")
    proficiency: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # beginner | intermediate | advanced | expert

    session: Mapped["Session"] = relationship("Session", back_populates="skills")


from models.session import Session
