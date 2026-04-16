"""FastAPI main application."""

import asyncio
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import settings
from db import init_db
from middleware.rate_limit import rate_limiter, AI_PATHS, get_client_key


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)

        if path == "/api/health":
            return await call_next(request)

        client_key = get_client_key(request)

        is_ai = any(ai_path in path for ai_path in AI_PATHS)
        is_login = "/api/auth/login" in path
        is_admin = "/api/activation/admin" in path
        is_get = request.method == "GET"

        if is_admin:
            admin_key = request.headers.get("X-Admin-Key", "none")
            allowed = await rate_limiter.check_admin(f"admin:{admin_key}")
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "管理员操作过于频繁"},
                )
            return await call_next(request)

        if is_login:
            allowed = await rate_limiter.check_login(f"login:{client_key}")
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "登录尝试过于频繁，请15分钟后再试"},
                )
            return await call_next(request)

        allowed = await rate_limiter.check(client_key, is_ai=is_ai, is_get=is_get)
        if not allowed:
            retry_after = await rate_limiter.get_retry_after(client_key, is_ai=is_ai, is_get=is_get)
            return JSONResponse(
                status_code=429,
                content={"detail": "操作过于频繁，请稍后再试"},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    # Reset stuck tasks from previous crashes
    from sqlalchemy import select, update
    from models.material import Material
    from models.review_session import ReviewSession
    from db import AsyncSessionLocal
    import logging
    logger = logging.getLogger(__name__)
    async with AsyncSessionLocal() as db:
        stuck_materials = await db.execute(
            update(Material).where(Material.analysis_status == "analyzing")
            .values(analysis_status="pending")
        )
        stuck_reviews = await db.execute(
            update(ReviewSession).where(ReviewSession.status == "running")
            .values(status="pending")
        )
        await db.commit()

    from tasks.v2_analyze import enqueue_analysis
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Material).where(Material.analysis_status == "pending")
        )
        pending = result.scalars().all()
        for m in pending:
            enqueue_analysis(m.id)
        if pending:
            logger.info(f"Re-enqueued {len(pending)} pending material analyses")

    yield


app = FastAPI(
    title="ResumeForge API",
    description="AI-powered resume building tool",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Key"],
)

app.add_middleware(RateLimitMiddleware)

if settings.require_activation == "true":
    from middleware.activation import ActivationMiddleware
    app.add_middleware(ActivationMiddleware)

from api import auth, activation, materials, jds, v2_analyze, v2_resumes, v2_reviews

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(activation.router, prefix="/api/activation", tags=["activation"])
app.include_router(materials.router, prefix="/api/materials", tags=["materials"])
app.include_router(jds.router, prefix="/api/jds", tags=["jds"])
app.include_router(v2_analyze.router, prefix="/api/materials", tags=["v2_analyze"])
app.include_router(v2_resumes.router, prefix="/api/resumes", tags=["v2_resumes"])
app.include_router(v2_reviews.router, prefix="/api/reviews", tags=["v2_reviews"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
