"""Activation middleware — strict allowlist.

Only explicitly public paths are allowed without activation.
All POST/PUT/DELETE to /api/ require a valid device activation.
GET requests are allowed (reads don't consume AI resources).
"""

from datetime import datetime

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# These paths are publicly accessible without activation
PUBLIC_PATHS = [
    "/api/health",
    "/api/activation/activate",
    "/api/activation/status",
    "/api/activation/unbind",
    "/api/activation/admin",
]

# Paths that consume AI resources — also blocked for GET when strict mode is needed
AI_HEAVY_PATHS = [
    "/analyze",
    "/match",
    "/generate",
    "/optimize",
    "/ats-score",
    "/jd-parse",
    "/merge",
    "/rewrite",
]


class ActivationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Non-API paths (static files, frontend routes) — always allow
        if not path.startswith("/api/"):
            return await call_next(request)

        # Public API paths — always allow
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        # GET requests — allow (reads don't consume AI resources)
        if request.method == "GET":
            return await call_next(request)

        # All other write operations require activation
        device_id = request.headers.get("X-Device-ID")
        if not device_id:
            return JSONResponse(
                status_code=401, content={"detail": "Device ID required"}
            )

        from db import AsyncSessionLocal
        from models.activation import ActivationCode, DeviceActivation
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(DeviceActivation).where(
                    DeviceActivation.device_id == device_id
                )
            )
            activation = result.scalar_one_or_none()

            if not activation:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "请先激活 ResumeForge"},
                )

            # Check if the associated activation code is still valid
            code_result = await db.execute(
                select(ActivationCode).where(
                    ActivationCode.id == activation.code_id
                )
            )
            code = code_result.scalar_one_or_none()

            if code and not code.is_active:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "激活码已被禁用"},
                )

            if code and code.expires_at:
                if datetime.now() > code.expires_at:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "激活码已过期，请续费"},
                    )

            # Check device limit
            if code:
                device_count_result = await db.execute(
                    select(DeviceActivation)
                    .where(DeviceActivation.code_id == code.id)
                )
                all_activations = device_count_result.scalars().all()
                active_device_ids = {da.device_id for da in all_activations}
                if device_id not in active_device_ids and len(active_device_ids) >= code.max_devices:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": f"激活码已达最大设备数（{code.max_devices}）"},
                    )

            activation.last_active_at = datetime.now()
            await db.commit()

        return await call_next(request)
