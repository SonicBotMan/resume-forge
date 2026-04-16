from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from db import Base


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    jd_text: Mapped[str] = mapped_column(Text)
    parsed_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_parsed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
