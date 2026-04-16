"""Activation models."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base


class ActivationCode(Base):
    __tablename__ = "activation_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    code_type: Mapped[str] = mapped_column(String(20))  # single, duo, family, trial
    max_devices: Mapped[int] = mapped_column(Integer, default=1)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    activations: Mapped[List["DeviceActivation"]] = relationship(
        "DeviceActivation", back_populates="code", cascade="all, delete-orphan"
    )


class DeviceActivation(Base):
    __tablename__ = "device_activations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code_id: Mapped[str] = mapped_column(String(36), ForeignKey("activation_codes.id"))
    device_id: Mapped[str] = mapped_column(String(100))  # 设备指纹
    device_name: Mapped[Optional[str]] = mapped_column(String(100))
    activated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_active_at: Mapped[datetime] = mapped_column(DateTime)

    code: Mapped["ActivationCode"] = relationship(
        "ActivationCode", back_populates="activations"
    )
