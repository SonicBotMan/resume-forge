"""Activation service."""

import secrets
import string
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

CODE_FORMAT = "RF-{year}{batch}{random}"
SAFE_CHARS = string.ascii_uppercase + string.digits
SAFE_CHARS = SAFE_CHARS.replace("O", "").replace("I", "")

CODE_TYPES = {
    "single": {"name": "单人版", "max_devices": 1, "expires_days": None},
    "duo": {"name": "双人版", "max_devices": 2, "expires_days": None},
    "family": {"name": "家庭版", "max_devices": 5, "expires_days": None},
    "trial": {"name": "试用版", "max_devices": 1, "expires_days": 7},
}


def generate_activation_code(
    code_type: str = "single", year: int = None, batch: str = "A"
) -> str:
    """Generate an activation code."""
    if year is None:
        year = datetime.now().year
    random_part = "".join(secrets.choice(SAFE_CHARS) for _ in range(6))
    return f"RF-{year}{batch}{random_part}"


def validate_code_format(code: str) -> bool:
    """Validate code format."""
    import re

    pattern = r"^RF-\d{4}[A-Z][A-Z0-9]{6}$"
    return bool(re.match(pattern, code.upper()))


def check_activation_valid(code_record, device_id: str) -> Dict[str, Any]:
    """Check if activation is valid."""
    if not code_record:
        return {"valid": False, "error": "激活码不存在"}

    if not code_record.is_active:
        return {"valid": False, "error": "激活码已停用"}

    if code_record.expires_at and code_record.expires_at < datetime.now():
        return {"valid": False, "error": "激活码已过期"}

    current_activations = len(code_record.activations)

    if current_activations >= code_record.max_devices:
        # Check if this device is already activated
        for act in code_record.activations:
            if act.device_id == device_id:
                return {"valid": True, "reactivated": True, "activation": act}
        return {"valid": False, "error": "设备数已达上限"}

    return {"valid": True}


def create_activation(
    code_record, device_id: str, device_name: str = None
) -> Dict[str, Any]:
    """Create a new activation."""
    validation = check_activation_valid(code_record, device_id)

    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}

    if validation.get("reactivated"):
        # Update last active time
        activation = validation["activation"]
        activation.last_active_at = datetime.now()
        if device_name:
            activation.device_name = device_name
        return {"success": True, "reactivated": True, "activation_id": activation.id}

    # Create new activation
    activation = {
        "id": str(uuid.uuid4()),
        "code_id": code_record.id,
        "device_id": device_id,
        "device_name": device_name,
        "activated_at": datetime.now(),
        "last_active_at": datetime.now(),
    }

    return {"success": True, "activation": activation}


def get_activation_status(code_record) -> Dict[str, Any]:
    """Get activation status."""
    if not code_record:
        return {"exists": False}

    activations = code_record.activations or []

    return {
        "exists": True,
        "is_active": code_record.is_active,
        "code_type": code_record.code_type,
        "max_devices": code_record.max_devices,
        "used_devices": len(activations),
        "remaining_devices": code_record.max_devices - len(activations),
        "expires_at": code_record.expires_at.isoformat()
        if code_record.expires_at
        else None,
        "devices": [
            {
                "device_id": act.device_id,
                "device_name": act.device_name,
                "activated_at": act.activated_at.isoformat()
                if act.activated_at
                else None,
                "last_active_at": act.last_active_at.isoformat()
                if act.last_active_at
                else None,
            }
            for act in activations
        ],
    }
