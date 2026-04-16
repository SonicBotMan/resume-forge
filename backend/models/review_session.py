from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from db import Base


class ReviewSession(Base):
    __tablename__ = "review_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    resume_id: Mapped[str] = mapped_column(String(36), index=True)  # base_resume_id or targeted_resume_id
    resume_type: Mapped[str] = mapped_column(String(20))  # "base" or "targeted"
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/running/completed/failed

    hr_review: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    headhunter_review: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    interviewer_review: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_review: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expert_review: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    synthesis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    interview_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
