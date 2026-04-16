from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, Float, func
from sqlalchemy.orm import Mapped, mapped_column
from db import Base


class MaterialAnalysis(Base):
    __tablename__ = "material_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    material_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)

    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    projects_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skills_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    achievements_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    education_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    experience_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_chunks_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
