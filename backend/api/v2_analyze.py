"""V2 Analysis API - Material-based analysis with polling support."""

import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from db import get_db, Material as MaterialModel, MaterialAnalysis as MaterialAnalysisModel
from api.auth import get_current_user_id
from tasks.v2_analyze import enqueue_analysis
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


async def verify_material_access(
    material_id: str,
    user_id: str,
    db: AsyncSession,
) -> MaterialModel:
    result = await db.execute(
        select(MaterialModel).where(MaterialModel.id == material_id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="资料不存在")
    if material.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问此资料")
    return material


class AnalyzeResponse(BaseModel):
    material_id: str
    status: str
    message: str


class BatchAnalyzeRequest(BaseModel):
    material_ids: List[str]


class BatchAnalyzeResponse(BaseModel):
    accepted: List[str]
    rejected: List[str]
    message: str


class StatusResponse(BaseModel):
    material_id: str
    status: str
    message: Optional[str] = None
    error: Optional[str] = None


class AnalysisResponse(BaseModel):
    material_id: str
    status: str
    summary: Optional[str] = None
    projects: Optional[List[dict]] = None
    skills: Optional[List[dict]] = None
    achievements: Optional[List[dict]] = None
    education: Optional[List[dict]] = None
    experience: Optional[List[dict]] = None
    confidence: float = 0.0


@router.post("/{material_id}/analyze", response_model=AnalyzeResponse)
async def start_material_analysis(
    material_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    material = await verify_material_access(material_id, user_id, db)
    
    if material.analysis_status == "analyzing":
        return AnalyzeResponse(
            material_id=material_id,
            status="analyzing",
            message="Analysis already in progress",
        )
    
    await db.execute(
        update(MaterialModel)
        .where(MaterialModel.id == material_id)
        .values(analysis_status="pending", analysis_error=None)
    )
    await db.commit()
    
    enqueue_analysis(material_id)
    
    return AnalyzeResponse(
        material_id=material_id,
        status="started",
        message="分析已开始",
    )


@router.post("/batch-analyze", response_model=BatchAnalyzeResponse)
async def batch_analyze_materials(
    request: BatchAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    if len(request.material_ids) > 10:
        raise HTTPException(status_code=400, detail="最多同时分析10个资料")
    
    accepted = []
    rejected = []
    
    for material_id in request.material_ids:
        try:
            result = await db.execute(
                select(MaterialModel).where(MaterialModel.id == material_id)
            )
            material = result.scalar_one_or_none()
            
            if not material:
                rejected.append(material_id)
                continue
            
            if material.user_id != user_id:
                rejected.append(material_id)
                continue
            
            if material.analysis_status == "analyzing":
                accepted.append(material_id)
                continue
            
            await db.execute(
                update(MaterialModel)
                .where(MaterialModel.id == material_id)
                .values(analysis_status="pending", analysis_error=None)
            )
            accepted.append(material_id)
            
        except Exception as e:
            logger.error(f"Error processing material {material_id}: {e}")
            rejected.append(material_id)
    
    await db.commit()
    
    for material_id in accepted:
        if not material_id.startswith("skip"):
            enqueue_analysis(material_id)
    
    return BatchAnalyzeResponse(
        accepted=accepted,
        rejected=rejected,
        message=f"Started analysis for {len(accepted)} materials",
    )


@router.get("/{material_id}/analyze/status", response_model=StatusResponse)
async def get_analysis_status(
    material_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    material = await verify_material_access(material_id, user_id, db)
    
    return StatusResponse(
        material_id=material_id,
        status=material.analysis_status,
        error=material.analysis_error,
    )


@router.post("/{material_id}/analyze/retry", response_model=AnalyzeResponse)
async def retry_analysis(
    material_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    material = await verify_material_access(material_id, user_id, db)
    
    if material.analysis_status == "analyzing":
        return AnalyzeResponse(
            material_id=material_id,
            status="analyzing",
            message="Analysis already in progress",
        )
    
    await db.execute(
        update(MaterialModel)
        .where(MaterialModel.id == material_id)
        .values(analysis_status="pending", analysis_error=None)
    )
    await db.commit()
    
    enqueue_analysis(material_id)
    
    return AnalyzeResponse(
        material_id=material_id,
        status="restarted",
        message="Analysis restarted",
    )


@router.get("/{material_id}/analysis", response_model=AnalysisResponse)
async def get_analysis_result(
    material_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    material = await verify_material_access(material_id, user_id, db)
    
    result = await db.execute(
        select(MaterialAnalysisModel).where(MaterialAnalysisModel.material_id == material_id)
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        return AnalysisResponse(
            material_id=material_id,
            status=material.analysis_status,
            confidence=0.0,
        )
    
    return AnalysisResponse(
        material_id=material_id,
        status=material.analysis_status,
        summary=analysis.summary,
        projects=json.loads(analysis.projects_json) if analysis.projects_json else None,
        skills=json.loads(analysis.skills_json) if analysis.skills_json else None,
        achievements=json.loads(analysis.achievements_json) if analysis.achievements_json else None,
        education=json.loads(analysis.education_json) if analysis.education_json else None,
        experience=json.loads(analysis.experience_json) if analysis.experience_json else None,
        confidence=analysis.confidence,
    )
