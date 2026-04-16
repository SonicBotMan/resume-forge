"""Material model - User-level persistent material library."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from db import Base


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(20))  # pdf/docx/pptx/txt/image/text_input

    # File-based materials
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Text-based materials (direct input)
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Analysis status
    analysis_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/analyzing/success/failed
    analysis_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
