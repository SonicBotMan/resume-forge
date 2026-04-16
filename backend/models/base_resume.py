from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from db import Base


class BaseResume(Base):
    __tablename__ = "base_resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: summary/experience/projects/skills/education
    version: Mapped[int] = mapped_column(Integer, default=1)
    source_material_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    generation_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/generating/success/failed
    generation_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
