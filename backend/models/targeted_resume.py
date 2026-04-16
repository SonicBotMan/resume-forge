from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from db import Base


class TargetedResume(Base):
    __tablename__ = "targeted_resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    jd_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    match_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    adjustment_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    generation_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/generating/success/failed
    generation_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
