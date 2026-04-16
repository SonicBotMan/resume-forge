"""File model."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    upload_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    parse_status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending | parsing | done | error
    parse_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    session: Mapped["Session"] = relationship("Session", back_populates="files")
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk", back_populates="file", cascade="all, delete-orphan"
    )


from models.session import Session
from models.chunk import Chunk
