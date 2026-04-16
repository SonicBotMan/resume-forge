import uuid
import html
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from db import get_db, JobDescription
from api.auth import get_current_user_id
from api.deps import get_owned
from services.ai.pipeline import parse_jd

router = APIRouter()


class JDCreateRequest(BaseModel):
    title: str
    company: Optional[str] = None
    jd_text: str


class JDUpdateRequest(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    jd_text: Optional[str] = None


class JDResponse(BaseModel):
    id: str
    user_id: str
    title: str
    company: Optional[str]
    jd_text: str
    parsed_data: Optional[str]
    is_parsed: bool
    created_at: str
    updated_at: str


class JDParseResponse(BaseModel):
    id: str
    parsed_data: dict
    is_parsed: bool


@router.post("", response_model=JDResponse)
async def create_jd(
    request: JDCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    if len(request.jd_text) > 10000:
        raise HTTPException(status_code=400, detail="JD text too large (max 10000 characters)")

    if len(request.title) > 255:
        raise HTTPException(status_code=400, detail="Title too long (max 255 characters)")

    if request.company and len(request.company) > 255:
        raise HTTPException(status_code=400, detail="Company name too long (max 255 characters)")

    jd_id = str(uuid.uuid4())
    jd = JobDescription(
        id=jd_id,
        user_id=user_id,
        title=html.escape(request.title[:255]),
        company=html.escape(request.company[:255]) if request.company else None,
        jd_text=request.jd_text,
        is_parsed=False,
    )
    db.add(jd)
    await db.flush()
    await db.refresh(jd)

    return JDResponse(
        id=jd.id,
        user_id=jd.user_id,
        title=jd.title,
        company=jd.company,
        jd_text=jd.jd_text,
        parsed_data=jd.parsed_data,
        is_parsed=jd.is_parsed,
        created_at=jd.created_at.isoformat(),
        updated_at=jd.updated_at.isoformat(),
    )


@router.get("")
async def list_jds(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    offset = (page - 1) * page_size

    count_result = await db.execute(
        select(func.count()).where(JobDescription.user_id == user_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(JobDescription)
        .where(JobDescription.user_id == user_id)
        .order_by(JobDescription.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    jds = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 1,
        "items": [
            {
                "id": jd.id,
                "user_id": jd.user_id,
                "title": jd.title,
                "company": jd.company,
                "jd_text": jd.jd_text,
                "parsed_data": jd.parsed_data,
                "is_parsed": jd.is_parsed,
                "created_at": jd.created_at.isoformat(),
                "updated_at": jd.updated_at.isoformat(),
            }
            for jd in jds
        ],
    }


@router.get("/{jd_id}", response_model=JDResponse)
async def get_jd(
    jd_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    jd = await get_owned(JobDescription, jd_id, user_id, db)

    return JDResponse(
        id=jd.id,
        user_id=jd.user_id,
        title=jd.title,
        company=jd.company,
        jd_text=jd.jd_text,
        parsed_data=jd.parsed_data,
        is_parsed=jd.is_parsed,
        created_at=jd.created_at.isoformat(),
        updated_at=jd.updated_at.isoformat(),
    )


@router.put("/{jd_id}", response_model=JDResponse)
async def update_jd(
    jd_id: str,
    request: JDUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    jd = await get_owned(JobDescription, jd_id, user_id, db)

    if request.title is not None:
        if len(request.title) > 255:
            raise HTTPException(status_code=400, detail="Title too long (max 255 characters)")
        jd.title = html.escape(request.title[:255])
    
    if request.company is not None:
        if len(request.company) > 255:
            raise HTTPException(status_code=400, detail="Company name too long (max 255 characters)")
        jd.company = html.escape(request.company[:255]) if request.company else None
    
    if request.jd_text is not None:
        if len(request.jd_text) > 10000:
            raise HTTPException(status_code=400, detail="JD text too large (max 10000 characters)")
        jd.jd_text = request.jd_text
        jd.is_parsed = False
        jd.parsed_data = None

    await db.commit()
    await db.refresh(jd)

    return JDResponse(
        id=jd.id,
        user_id=jd.user_id,
        title=jd.title,
        company=jd.company,
        jd_text=jd.jd_text,
        parsed_data=jd.parsed_data,
        is_parsed=jd.is_parsed,
        created_at=jd.created_at.isoformat(),
        updated_at=jd.updated_at.isoformat(),
    )


@router.delete("/{jd_id}")
async def delete_jd(
    jd_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    jd = await get_owned(JobDescription, jd_id, user_id, db)

    await db.delete(jd)
    await db.commit()

    return {"status": "deleted"}


@router.post("/{jd_id}/parse", response_model=JDParseResponse)
async def parse_jd_endpoint(
    jd_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    jd = await get_owned(JobDescription, jd_id, user_id, db)

    if jd.is_parsed and jd.parsed_data:
        import json
        parsed_data = json.loads(jd.parsed_data) if isinstance(jd.parsed_data, str) else jd.parsed_data
        return JDParseResponse(
            id=jd.id,
            parsed_data=parsed_data,
            is_parsed=True,
        )

    import json
    parsed_data = await parse_jd(jd.jd_text)
    
    jd.parsed_data = json.dumps(parsed_data, ensure_ascii=False)
    jd.is_parsed = True
    await db.commit()
    await db.refresh(jd)

    return JDParseResponse(
        id=jd.id,
        parsed_data=parsed_data,
        is_parsed=True,
    )
