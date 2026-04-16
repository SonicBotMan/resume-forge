"""V2 analysis task for processing materials - Material-based analysis."""

import json
import uuid
import asyncio
import logging
from typing import Dict, Any, List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db import async_engine, AsyncSessionLocal
from models.material import Material
from models.material_analysis import MaterialAnalysis
from services.parser.markitdown_parser import MarkItDownParser
from services.parser.text_parser import TextParser
from services.chunker import Chunker
from services.ai.client import llm_client
from services.ai.prompts.classify import get_classify_prompt
from services.ai.prompts.extract import get_extract_prompt

logger = logging.getLogger(__name__)

_analysis_queue: list[str] = []
_queue_running = False


def enqueue_analysis(material_id: str):
    _analysis_queue.append(material_id)
    _try_start_worker()


def _try_start_worker():
    global _queue_running
    if _queue_running:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    _queue_running = True
    loop.create_task(_analysis_worker())


async def _analysis_worker():
    global _queue_running
    try:
        while _analysis_queue:
            material_id = _analysis_queue.pop(0)
            try:
                await asyncio.wait_for(analyze_material(material_id), timeout=600)
            except asyncio.TimeoutError:
                logger.error(f"Analysis timed out after 300s for {material_id}")
                async with AsyncSessionLocal() as db:
                    await db.execute(
                        update(Material)
                        .where(Material.id == material_id)
                        .values(analysis_status="failed", analysis_error="分析超时，请稍后重试")
                    )
                    await db.commit()
            except Exception as e:
                logger.error(f"Queue worker error for {material_id}: {e}", exc_info=True)
    finally:
        _queue_running = False


_md_parser = MarkItDownParser()

PARSERS = {
    "pdf": _md_parser,
    "pptx": _md_parser,
    "ppt": _md_parser,
    "docx": _md_parser,
    "doc": _md_parser,
    "xlsx": _md_parser,
    "xls": _md_parser,
    "txt": _md_parser,
    "text": _md_parser,
    "md": _md_parser,
    "html": _md_parser,
    "csv": _md_parser,
    "json": _md_parser,
    "image": _md_parser,
    "audio": _md_parser,
}


def _serialize_value(val: Any) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, dict):
        return json.dumps(val, ensure_ascii=False)
    if isinstance(val, list):
        return json.dumps(val, ensure_ascii=False)
    return str(val)


async def _classify_chunk(content: str) -> dict:
    classify_prompt = get_classify_prompt(content)
    result = await llm_client.structured_output(
        classify_prompt,
        {"categories": [], "relevance": 0.0, "brief_summary": ""},
    )
    return {
        "content": content,
        "categories": result.get("categories", []),
        "relevance": result.get("relevance", 0.0),
        "summary": result.get("brief_summary", ""),
    }


async def _extract_chunk(content: str) -> dict:
    extract_prompt = get_extract_prompt(content)
    result = await llm_client.structured_output(
        extract_prompt,
        {
            "personal_info": {"name": "", "phone": "", "email": "", "location": ""},
            "work_experience": [],
            "projects": [],
            "education": [],
            "skills_mentioned": [],
            "tools_mentioned": [],
            "achievements": [],
        },
    )
    return result


async def _update_material_status(
    db: AsyncSession,
    material_id: str,
    status: str,
    progress: float = 0.0,
    message: str = "",
    error: str = None,
):
    await db.execute(
        update(Material)
        .where(Material.id == material_id)
        .values(
            analysis_status=status,
            analysis_error=error,
        )
    )
    await db.commit()


async def analyze_material(material_id: str):
    try:
        source_type = None
        async with AsyncSession(async_engine) as db:
            result = await db.execute(
                select(Material).where(Material.id == material_id)
            )
            material = result.scalar_one_or_none()
            
            if not material:
                logger.error(f"Material not found: {material_id}")
                return
            
            source_type = material.source_type
            
            await _update_material_status(
                db, material_id, "analyzing", 0.1, "Starting analysis"
            )
        
        if source_type == "text_input":
            await _analyze_text_material(material_id)
        else:
            await _analyze_file_material(material_id)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        async with AsyncSession(async_engine) as db:
            await _update_material_status(
                db, material_id, "failed", 0.0, "", str(e)
            )


async def _analyze_text_material(material_id: str):
    user_id = None
    text_content = None
    
    async with AsyncSession(async_engine) as db:
        result = await db.execute(
            select(Material).where(Material.id == material_id)
        )
        material = result.scalar_one_or_none()
        
        if not material:
            logger.error(f"Material not found: {material_id}")
            return
        
        user_id = material.user_id
        text_content = material.text_content
        
        await _update_material_status(
            db, material_id, "analyzing", 0.3, "Processing text content"
        )
    
    chunks_data = [{"content": text_content}]
    
    async with AsyncSession(async_engine) as db:
        await _extract_from_chunks(
            db,
            material_id,
            user_id,
            chunks_data,
        )


async def _analyze_file_material(material_id: str):
    user_id = None
    file_path = None
    source_type = None
    
    async with AsyncSession(async_engine) as db:
        result = await db.execute(
            select(Material).where(Material.id == material_id)
        )
        material = result.scalar_one_or_none()
        
        if not material:
            logger.error(f"Material not found: {material_id}")
            return
        
        user_id = material.user_id
        file_path = material.file_path
        source_type = material.source_type
        
        parser = PARSERS.get(source_type)
        if not parser:
            await _update_material_status(
                db, material_id, "failed", 0.0, "",
                f"No parser for type: {source_type}"
            )
            return
        
        await _update_material_status(
            db, material_id, "analyzing", 0.2, "Parsing file"
        )
    
    parsed_doc = await parser.parse(file_path)
    
    chunker = Chunker()
    chunks = chunker.chunk_by_document_structure(parsed_doc)
    
    chunks_data = [{"content": chunk["content"]} for chunk in chunks]
    
    async with AsyncSession(async_engine) as db:
        await _extract_from_chunks(
            db,
            material_id,
            user_id,
            chunks_data,
        )


async def _extract_from_chunks(
    db: AsyncSession,
    material_id: str,
    user_id: str,
    chunks_data: List[Dict[str, Any]],
):
    """Extract projects, skills, achievements from chunks."""
    
    await _update_material_status(
        db, material_id, "analyzing", 0.4, "Classifying chunks"
    )
    
    classify_results = []
    for c in chunks_data:
        try:
            r = await _classify_chunk(c["content"])
            classify_results.append(r)
        except Exception as e:
            logger.error(f"Classification error: {e}")
            classify_results.append(None)
    
    relevant_chunks = []
    summaries = []
    raw_chunks = []
    
    for i, result in enumerate(classify_results):
        if result is None:
            continue
        
        categories = result.get("categories", [])
        if any(cat in ["A", "B", "C", "D", "E", "F"] for cat in categories):
            relevant_chunks.append(chunks_data[i]["content"])
            summaries.append(result.get("summary", ""))
        raw_chunks.append({
            "content": chunks_data[i]["content"],
            "categories": result.get("categories", []),
            "relevance": result.get("relevance", 0.0),
            "summary": result.get("summary", ""),
        })
    
    await _update_material_status(
        db, material_id, "analyzing", 0.5,
        f"Extracting from {len(relevant_chunks)} relevant chunks"
    )
    
    extract_results = []
    for c in relevant_chunks:
        try:
            r = await _extract_chunk(c)
            extract_results.append(r)
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            extract_results.append(None)
    
    all_projects = []
    all_skills = []
    all_achievements = []
    all_education = []
    all_experience = []
    all_personal_info = []
    
    for result in extract_results:
        if result is None:
            continue
        
        personal = result.get("personal_info")
        if personal and any(personal.values()):
            all_personal_info.append(personal)
        
        for exp in result.get("work_experience", []):
            if exp.get("company"):
                all_experience.append({
                    "company": exp.get("company", ""),
                    "position": exp.get("position", ""),
                    "department": exp.get("department"),
                    "period": exp.get("period", ""),
                    "highlights": exp.get("highlights", []),
                })
        
        for proj_data in result.get("projects", []):
            result_val = proj_data.get("result")
            
            all_projects.append({
                "name": proj_data.get("name", "Unknown Project"),
                "role": proj_data.get("role"),
                "situation": proj_data.get("situation"),
                "task": proj_data.get("task"),
                "action": proj_data.get("action"),
                "result": _serialize_value(result_val),
                "description": proj_data.get("result"),
                "start_date": proj_data.get("time_range", {}).get("start") if isinstance(proj_data.get("time_range"), dict) else None,
                "end_date": proj_data.get("time_range", {}).get("end") if isinstance(proj_data.get("time_range"), dict) else None,
            })
        
        for edu in result.get("education", []):
            if edu.get("school") or edu.get("major"):
                all_education.append({
                    "school": edu.get("school", ""),
                    "major": edu.get("major", ""),
                    "degree": edu.get("degree", ""),
                    "period": edu.get("period", ""),
                })
        
        for skill_name in result.get("skills_mentioned", []):
            all_skills.append({
                "name": str(skill_name).strip(),
                "category": "skill",
            })
        
        for tool_name in result.get("tools_mentioned", []):
            all_skills.append({
                "name": str(tool_name).strip(),
                "category": "tool",
            })
        
        for achievement_text in result.get("achievements", []):
            all_achievements.append({
                "description": str(achievement_text),
            })
    
    await _update_material_status(
        db, material_id, "analyzing", 0.9, "Saving results"
    )
    
    await db.execute(
        delete(MaterialAnalysis).where(MaterialAnalysis.material_id == material_id)
    )
    await db.commit()
    
    seen_companies = set()
    deduped_experience = []
    for exp in all_experience:
        key = f"{exp.get('company','')}|{exp.get('position','')}".lower().strip()
        if key and key not in seen_companies:
            seen_companies.add(key)
            deduped_experience.append(exp)
        elif key in seen_companies:
            for existing in deduped_experience:
                ekey = f"{existing.get('company','')}|{existing.get('position','')}".lower().strip()
                if ekey == key:
                    if exp.get("highlights"):
                        existing["highlights"] = list(set(
                            (existing.get("highlights") or []) + exp.get("highlights", [])
                        ))
                    break

    seen_edu = set()
    deduped_education = []
    for edu in all_education:
        key = f"{edu.get('school','')}|{edu.get('major','')}".lower().strip()
        if key and key not in seen_edu:
            seen_edu.add(key)
            deduped_education.append(edu)

    merged_personal = {}
    for p in all_personal_info:
        for k, v in p.items():
            if v and not merged_personal.get(k):
                merged_personal[k] = v

    analysis = MaterialAnalysis(
        id=str(uuid.uuid4()),
        material_id=material_id,
        user_id=user_id,
        summary="\n".join(summaries) if summaries else None,
        projects_json=json.dumps(all_projects, ensure_ascii=False) if all_projects else None,
        skills_json=json.dumps(all_skills, ensure_ascii=False) if all_skills else None,
        achievements_json=json.dumps(all_achievements, ensure_ascii=False) if all_achievements else None,
        education_json=json.dumps(deduped_education, ensure_ascii=False) if deduped_education else None,
        experience_json=json.dumps(deduped_experience, ensure_ascii=False) if deduped_experience else None,
        raw_chunks_json=json.dumps(raw_chunks, ensure_ascii=False) if raw_chunks else None,
        confidence=0.8 if (all_projects or all_skills or all_achievements or deduped_experience or deduped_education) else 0.0,
    )
    db.add(analysis)
    await db.commit()
    
    from datetime import datetime
    await db.execute(
        update(Material)
        .where(Material.id == material_id)
        .values(
            analysis_status="success",
            analyzed_at=datetime.now(),
        )
    )
    await db.commit()
