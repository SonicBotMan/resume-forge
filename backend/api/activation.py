"""Activation API."""

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.activation import ActivationCode, DeviceActivation
from services.activation import (
    validate_code_format,
    check_activation_valid,
    get_activation_status,
    CODE_TYPES,
    generate_activation_code,
)
from sqlalchemy.orm import selectinload
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

ADMIN_KEY = os.environ.get("ADMIN_KEY")


async def get_db_session():
    async for db in get_db():
        yield db


class ActivateRequest(BaseModel):
    code: str
    device_id: str
    device_name: Optional[str] = None


class ActivationResponse(BaseModel):
    success: bool
    message: str
    code_type: Optional[str] = None
    max_devices: Optional[int] = None
    remaining_devices: Optional[int] = None


class DeviceInfo(BaseModel):
    device_id: str
    device_name: Optional[str]
    activated_at: Optional[str]
    last_active_at: Optional[str]


class StatusResponse(BaseModel):
    activated: bool
    code_type: Optional[str] = None
    max_devices: Optional[int] = None
    remaining_devices: Optional[int] = None
    expires_at: Optional[str] = None
    devices: List[DeviceInfo] = []


class UnbindRequest(BaseModel):
    device_id: str


@router.post("/activate", response_model=ActivationResponse)
async def activate(
    request: ActivateRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Activate with code."""
    code = request.code.upper().strip()

    if not validate_code_format(code):
        return ActivationResponse(success=False, message="激活码格式无效")

    result = await db.execute(
        select(ActivationCode)
        .options(selectinload(ActivationCode.activations))
        .where(ActivationCode.code == code)
    )
    code_record = result.scalar_one_or_none()

    if not code_record:
        return ActivationResponse(success=False, message="激活码不存在")

    validation = check_activation_valid(code_record, request.device_id)

    if not validation["valid"]:
        return ActivationResponse(success=False, message=validation["error"])

    if validation.get("reactivated"):
        # Update existing activation
        result = await db.execute(
            select(DeviceActivation).where(
                DeviceActivation.code_id == code_record.id,
                DeviceActivation.device_id == request.device_id,
            )
        )
        activation_record = result.scalar_one_or_none()
        if activation_record:
            from datetime import datetime

            activation_record.last_active_at = datetime.now()
            if request.device_name:
                activation_record.device_name = request.device_name
            await db.commit()

        status = get_activation_status(code_record)
        return ActivationResponse(
            success=True,
            message="已重新激活",
            code_type=code_record.code_type,
            max_devices=code_record.max_devices,
            remaining_devices=status["remaining_devices"],
        )

    # Create new activation
    from datetime import datetime

    activation_record = DeviceActivation(
        id=str(uuid.uuid4()),
        code_id=code_record.id,
        device_id=request.device_id,
        device_name=request.device_name,
        activated_at=datetime.now(),
        last_active_at=datetime.now(),
    )
    db.add(activation_record)
    await db.commit()

    status = get_activation_status(code_record)
    return ActivationResponse(
        success=True,
        message="激活成功",
        code_type=code_record.code_type,
        max_devices=code_record.max_devices,
        remaining_devices=status["remaining_devices"],
    )


@router.get("/status/{device_id}", response_model=StatusResponse)
async def get_status(device_id: str, db: AsyncSession = Depends(get_db_session)):
    """Get activation status for device."""
    result = await db.execute(
        select(DeviceActivation).where(DeviceActivation.device_id == device_id)
    )
    activations = result.scalars().all()

    if not activations:
        return StatusResponse(activated=False)

    # Get the latest activation's code
    latest = activations[0]
    result = await db.execute(
        select(ActivationCode)
        .options(selectinload(ActivationCode.activations))
        .where(ActivationCode.id == latest.code_id)
    )
    code_record = result.scalar_one_or_none()

    if not code_record:
        return StatusResponse(activated=False)

    status = get_activation_status(code_record)

    return StatusResponse(
        activated=True,
        code_type=status["code_type"],
        max_devices=status["max_devices"],
        remaining_devices=status["remaining_devices"],
        expires_at=status["expires_at"],
        devices=[DeviceInfo(**d) for d in status["devices"]],
    )


@router.post("/unbind")
async def unbind(
    request: UnbindRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Unbind a device."""
    result = await db.execute(
        select(DeviceActivation).where(DeviceActivation.device_id == request.device_id)
    )
    activation_record = result.scalar_one_or_none()

    if not activation_record:
        raise HTTPException(status_code=404, detail="激活记录不存在")

    await db.delete(activation_record)
    await db.commit()

    return {"success": True, "message": "解绑成功"}


# Admin endpoints
@router.post("/admin/codes")
async def create_code(
    code_type: str = "single",
    db: AsyncSession = Depends(get_db_session),
    x_admin_key: str = Header(None),
):
    """Create activation code (admin)."""
    # Simple admin check (in production, use proper auth)
    if not ADMIN_KEY or x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="无权访问")

    if code_type not in CODE_TYPES:
        raise HTTPException(status_code=400, detail="无效的激活码类型")

    from datetime import datetime, timedelta

    config = CODE_TYPES[code_type]
    expires_at = None
    if config["expires_days"]:
        expires_at = datetime.now() + timedelta(days=config["expires_days"])

    code = generate_activation_code(code_type)

    record = ActivationCode(
        id=str(uuid.uuid4()),
        code=code,
        code_type=code_type,
        max_devices=config["max_devices"],
        expires_at=expires_at,
        is_active=True,
    )

    db.add(record)
    await db.commit()

    return {
        "success": True,
        "code": code,
        "code_type": code_type,
        "max_devices": config["max_devices"],
    }


@router.get("/admin/codes")
async def list_codes(
    db: AsyncSession = Depends(get_db_session),
    x_admin_key: str = Header(None),
):
    """List all codes (admin)."""
    if not ADMIN_KEY or x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="无权访问")

    result = await db.execute(select(ActivationCode))
    codes = result.scalars().all()

    return {
        "codes": [
            {
                "code": c.code,
                "code_type": c.code_type,
                "max_devices": c.max_devices,
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "expires_at": c.expires_at.isoformat() if c.expires_at else None,
            }
            for c in codes
        ]
    }
