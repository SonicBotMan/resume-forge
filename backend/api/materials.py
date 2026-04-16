import os
import uuid
import html
import math
import asyncio
import aiofiles
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from config import settings
from db import get_db, Material, MaterialAnalysis
from api.auth import get_current_user_id
from api.deps import get_owned

router = APIRouter()

ALLOWED_EXTENSIONS = {
    "pdf": "pdf",
    "pptx": "pptx",
    "ppt": "ppt",
    "docx": "docx",
    "doc": "doc",
    "xlsx": "xlsx",
    "xls": "xlsx",
    "txt": "text",
    "md": "text",
    "html": "html",
    "htm": "html",
    "csv": "csv",
    "json": "json",
    "png": "image",
    "jpg": "image",
    "jpeg": "image",
    "wav": "audio",
    "mp3": "audio",
}

MAGIC_SIGNATURES = {
    b"%PDF": "pdf",
    b"PK\x03\x04": "zip_based",
    b"\x89PNG": "png",
    b"\xff\xd8\xff": "jpg",
    b"\xff\xd8\xff\xe0": "jpg",
    b"\xff\xd8\xff\xe1": "jpg",
    b"RIFF": "wav",
    b"\x49\x44\x33": "mp3",
}


def get_file_type(filename: str) -> Optional[str]:
    safe_name = os.path.basename(filename)
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    return ALLOWED_EXTENSIONS.get(ext)


def verify_file_signature(content: bytes, declared_type: str) -> bool:
    if not content:
        return True
    header = content[:8]
    if declared_type == "pdf":
        return header.startswith(b"%PDF")
    if declared_type == "docx" or declared_type == "pptx":
        return header[:4] == b"PK\x03\x04"
    if declared_type == "image":
        return header[:4] in (b"\x89PNG", b"\xff\xd8") or header[:3] == b"\xff\xd8\xff"
    return True


class MaterialUploadResponse(BaseModel):
    id: str
    user_id: str
    name: str
    source_type: str
    file_path: Optional[str]
    file_size: Optional[int]
    text_content: Optional[str]
    analysis_status: str
    analysis_error: Optional[str]
    analyzed_at: Optional[str]
    created_at: str
    updated_at: str


class MaterialTextRequest(BaseModel):
    title: str
    content: str


class MaterialResponse(BaseModel):
    id: str
    user_id: str
    name: str
    source_type: str
    file_path: Optional[str]
    file_size: Optional[int]
    text_content: Optional[str]
    analysis_status: str
    analysis_error: Optional[str]
    analyzed_at: Optional[str]
    created_at: str
    updated_at: str


@router.post("/upload", response_model=MaterialUploadResponse)
async def upload_material(
    file: UploadFile = FastAPIFile(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    file_type = get_file_type(file.filename)
    if not file_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS.keys())}",
        )

    content_length = file.size
    if content_length and content_length > settings.max_file_size:
        raise HTTPException(status_code=400, detail="文件过大")

    material_id = str(uuid.uuid4())
    file_path = settings.upload_dir / "materials" / material_id
    file_path.parent.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(status_code=400, detail="文件过大")

    if not verify_file_signature(content, file_type):
        raise HTTPException(status_code=400, detail="文件内容与扩展名不匹配")

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    source_type = file_type if file_type in ["pdf", "docx", "pptx", "text", "xlsx", "html", "csv", "json"] else "image"

    material = Material(
        id=material_id,
        user_id=user_id,
        name=html.escape(file.filename[:255]),
        source_type=source_type,
        file_path=str(file_path),
        file_size=len(content),
        analysis_status="pending",
    )
    db.add(material)
    await db.flush()
    await db.refresh(material)

    return MaterialUploadResponse(
        id=material.id,
        user_id=material.user_id,
        name=material.name,
        source_type=material.source_type,
        file_path=material.file_path,
        file_size=material.file_size,
        text_content=material.text_content,
        analysis_status=material.analysis_status,
        analysis_error=material.analysis_error,
        analyzed_at=material.analyzed_at.isoformat() if material.analyzed_at else None,
        created_at=material.created_at.isoformat(),
        updated_at=material.updated_at.isoformat(),
    )


@router.post("/text", response_model=MaterialUploadResponse)
async def create_text_material(
    request: MaterialTextRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    if len(request.content) > 50000:
        raise HTTPException(status_code=400, detail="Content too large (max 50000 characters)")

    if len(request.title) > 255:
        raise HTTPException(status_code=400, detail="Title too long (max 255 characters)")

    material_id = str(uuid.uuid4())
    material = Material(
        id=material_id,
        user_id=user_id,
        name=html.escape(request.title[:255]),
        source_type="text_input",
        text_content=request.content,
        analysis_status="pending",
    )
    db.add(material)
    await db.flush()
    await db.refresh(material)

    return MaterialUploadResponse(
        id=material.id,
        user_id=material.user_id,
        name=material.name,
        source_type=material.source_type,
        file_path=material.file_path,
        file_size=material.file_size,
        text_content=material.text_content,
        analysis_status=material.analysis_status,
        analysis_error=material.analysis_error,
        analyzed_at=material.analyzed_at.isoformat() if material.analyzed_at else None,
        created_at=material.created_at.isoformat(),
        updated_at=material.updated_at.isoformat(),
    )


@router.get("")
async def list_materials(
    status: Optional[str] = Query(None, description="Filter by analysis status: pending, analyzing, success, failed"),
    type: Optional[str] = Query(None, description="Filter by source type: upload, text"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    offset = (page - 1) * page_size

    count_query = select(func.count()).where(Material.user_id == user_id)
    if status:
        count_query = count_query.where(Material.analysis_status == status)
    if type == "upload":
        upload_types = ["pdf", "docx", "pptx", "ppt", "doc", "image"]
        count_query = count_query.where(Material.source_type.in_(upload_types))
    elif type == "text":
        count_query = count_query.where(Material.source_type == "text_input")
    
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    query = (
        select(Material)
        .where(Material.user_id == user_id)
        .order_by(Material.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    if status:
        query = query.where(Material.analysis_status == status)
    if type == "upload":
        upload_types = ["pdf", "docx", "pptx", "ppt", "doc", "image"]
        query = query.where(Material.source_type.in_(upload_types))
    elif type == "text":
        query = query.where(Material.source_type == "text_input")

    result = await db.execute(query)
    materials = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 1,
        "items": [
            {
                "id": m.id,
                "user_id": m.user_id,
                "name": m.name,
                "source_type": m.source_type,
                "file_path": m.file_path,
                "file_size": m.file_size,
                "text_content": m.text_content,
                "analysis_status": m.analysis_status,
                "analysis_error": m.analysis_error,
                "analyzed_at": m.analyzed_at.isoformat() if m.analyzed_at else None,
                "created_at": m.created_at.isoformat(),
                "updated_at": m.updated_at.isoformat(),
            }
            for m in materials
        ],
    }


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    material = await get_owned(Material, material_id, user_id, db)

    return MaterialResponse(
        id=material.id,
        user_id=material.user_id,
        name=material.name,
        source_type=material.source_type,
        file_path=material.file_path,
        file_size=material.file_size,
        text_content=material.text_content,
        analysis_status=material.analysis_status,
        analysis_error=material.analysis_error,
        analyzed_at=material.analyzed_at.isoformat() if material.analyzed_at else None,
        created_at=material.created_at.isoformat(),
        updated_at=material.updated_at.isoformat(),
    )


@router.delete("/{material_id}")
async def delete_material(
    material_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    material = await get_owned(Material, material_id, user_id, db)

    file_path = material.file_path

    analysis_result = await db.execute(
        select(MaterialAnalysis).where(MaterialAnalysis.material_id == material_id)
    )
    analyses = analysis_result.scalars().all()
    
    for analysis in analyses:
        await db.delete(analysis)
    
    await db.delete(material)
    await db.commit()

    if file_path and os.path.exists(file_path):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, os.remove, file_path)

    return {"status": "deleted"}
