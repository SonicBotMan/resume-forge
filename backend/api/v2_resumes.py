import json
import math
import uuid
import html
import asyncio
import os
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional


def _remove_file(path: str):
    try:
        os.unlink(path)
    except OSError:
        pass

from db import get_db
from models.base_resume import BaseResume
from models.targeted_resume import TargetedResume
from models.job_description import JobDescription
from models.material import Material
from models.material_analysis import MaterialAnalysis
from api.auth import get_current_user_id
from api.deps import get_owned
from services.ai.client import llm_client
from tasks.generate_base_resume import generate_base_resume_task

router = APIRouter()


def sanitize_filename(name: str) -> str:
    import re
    name = re.sub(r'[^\w\s\-\u4e00-\u9fff]', '', name)
    return name[:80].strip() or "resume"


def filter_projects_by_selection(selected_names: list, all_projects: list) -> list:
    """Filter projects by LLM-selected names with fuzzy substring matching.

    Falls back to returning all projects if no matches are found,
    ensuring graceful degradation rather than an empty resume.
    """
    if not selected_names or not all_projects:
        return all_projects

    filtered = []
    seen = set()
    # Match in the order LLM selected (most relevant first)
    for sel in selected_names:
        if not sel:
            continue
        for p in all_projects:
            pname = p.get("name", "")
            if not pname or id(p) in seen:
                continue
            # Substring match in both directions handles minor variations
            if sel in pname or pname in sel:
                filtered.append(p)
                seen.add(id(p))
                break

    # If LLM's selections didn't match anything, fall back to all
    return filtered if filtered else all_projects


class UpdateResumeContent(BaseModel):
    content: str


class GenerateTargetedRequest(BaseModel):
    jd_id: str


@router.post("/base/generate")
async def generate_base_resume(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    result = await db.execute(
        select(MaterialAnalysis).where(
            MaterialAnalysis.user_id == user_id
        )
    )
    analyses = result.scalars().all()

    if not analyses:
        raise HTTPException(status_code=400, detail="请先分析至少一个资料")

    existing = await db.execute(
        select(BaseResume).where(BaseResume.user_id == user_id)
    )
    base = existing.scalar_one_or_none()

    if base and base.generation_status == "generating":
        return {"status": "generating", "message": "简历生成中，请稍后刷新查看结果"}

    if base and base.generation_status == "success" and base.source_material_ids:
        import json as _json
        try:
            old_ids = set(_json.loads(base.source_material_ids))
        except (json.JSONDecodeError, TypeError):
            old_ids = set()
        current_ids = {a.material_id for a in analyses}
        if old_ids == current_ids:
            base_updated = base.updated_at
            needs_update = False
            for a in analyses:
                if a.updated_at and a.updated_at > base_updated:
                    needs_update = True
                    break
                if a.created_at and a.created_at > base_updated:
                    needs_update = True
                    break
            if not needs_update:
                raise HTTPException(status_code=400, detail="资料无变化，无法重新生成")

    if base:
        base.generation_status = "pending"
        base.generation_error = None
        base.updated_at = datetime.now()
    else:
        base = BaseResume(
            id=str(uuid.uuid4()),
            user_id=user_id,
            version=0,
            generation_status="pending",
        )
        db.add(base)

    await db.flush()

    task = asyncio.create_task(generate_base_resume_task(user_id))
    task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)

    return {"status": "started", "message": "简历生成已开始，预计需要30-60秒，请稍后刷新页面查看结果"}


@router.get("/base")
async def get_base_resume(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    result = await db.execute(
        select(BaseResume).where(BaseResume.user_id == user_id)
    )
    base = result.scalar_one_or_none()
    if not base:
        return {"exists": False}
    
    response = {
        "exists": True,
        "id": base.id,
        "version": base.version,
        "generation_status": base.generation_status or "success",
        "source_material_ids": json.loads(base.source_material_ids) if base.source_material_ids else [],
        "updated_at": base.updated_at.isoformat(),
    }

    if base.generation_error:
        response["generation_error"] = base.generation_error

    if base.content:
        try:
            response["content"] = json.loads(base.content)
        except (json.JSONDecodeError, TypeError):
            response["content"] = {}
    else:
        response["content"] = None

    return response


@router.put("/base")
async def update_base_resume(
    req: UpdateResumeContent,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    result = await db.execute(
        select(BaseResume).where(BaseResume.user_id == user_id)
    )
    base = result.scalar_one_or_none()
    if not base:
        raise HTTPException(status_code=404, detail="底版简历不存在")
    try:
        json.loads(req.content)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail="无效的JSON内容")
    base.content = req.content
    base.version += 1
    base.updated_at = datetime.now()
    await db.flush()
    return {"id": base.id, "version": base.version}


MATCH_PROMPT = """你是一位资深的简历匹配分析师。请对比以下简历和目标岗位，给出专业的匹配分析。

简历内容：
{resume}

目标岗位信息：
{jd}

请返回JSON格式：
{{
    "grade": "A/B/C/D",
    "skill_match": {{
        "matched": ["匹配的技能1", "匹配的技能2"],
        "missing": ["缺失的技能1"],
        "rate": "80%"
    }},
    "experience_match": {{
        "matched": ["匹配的经历1"],
        "gap": ["不足的方面1"],
        "rate": "70%"
    }},
    "strengths": ["优势1", "优势2"],
    "risks": ["风险1", "风险2"],
    "recommendation": "投递/优化后再投递/不建议"
}}

评分标准：
- A: 强烈推荐投递（匹配度>80%）
- B: 建议投递（匹配度60-80%）
- C: 需要准备（匹配度40-60%）
- D: 不太匹配（匹配度<40%）"""


async def _generate_targeted_task(targeted_id: str, user_id: str, jd_id: str):
    from db import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TargetedResume).where(TargetedResume.id == targeted_id))
        targeted = result.scalar_one_or_none()
        if not targeted:
            return

        targeted.generation_status = "generating"
        await db.commit()

    try:
        async with AsyncSessionLocal() as db:
            base_result = await db.execute(select(BaseResume).where(BaseResume.user_id == user_id))
            base = base_result.scalar_one_or_none()
            if not base:
                raise Exception("底版简历不存在")

            jd_result = await db.execute(select(JobDescription).where(JobDescription.id == jd_id))
            jd = jd_result.scalar_one_or_none()
            if not jd:
                raise Exception("JD不存在")

        resume_data = json.loads(base.content)

        # Compress resume for LLM: full summary/experience/skills/education, project names only
        compressed = {}
        if resume_data.get("personal_info"):
            compressed["personal_info"] = resume_data["personal_info"]
        compressed["summary"] = resume_data.get("summary", "")
        compressed["experience"] = resume_data.get("experience", [])
        compressed["education"] = resume_data.get("education", [])
        compressed["skills"] = resume_data.get("skills", [])
        compressed["career_highlights"] = resume_data.get("career_highlights", [])

        projects = resume_data.get("projects", [])
        compressed["projects_count"] = len(projects)
        compressed["projects_sample"] = [
            {"name": p.get("name"), "role": p.get("role"), "period": f"{p.get('start_date','')}~{p.get('end_date','')}"}
            for p in projects[:20]
        ]

        resume_compact = json.dumps(compressed, ensure_ascii=False)

        # Use parsed JD data if available for precise matching
        jd_info = jd.jd_text
        if jd.is_parsed and jd.parsed_data:
            try:
                parsed = json.loads(jd.parsed_data) if isinstance(jd.parsed_data, str) else jd.parsed_data
                jd_info = json.dumps({
                    "title": jd.title,
                    "company": jd.company,
                    "required_skills": parsed.get("required_skills", []),
                    "preferred_skills": parsed.get("preferred_skills", []),
                    "seniority_level": parsed.get("seniority_level", ""),
                    "responsibilities": parsed.get("key_responsibilities", []),
                    "industry_keywords": parsed.get("industry_keywords", []),
                    "raw_text": jd.jd_text[:500],
                }, ensure_ascii=False)
            except (json.JSONDecodeError, TypeError):
                pass

        # Single LLM call: generate targeted resume + match grade + adjustment analysis
        gen_prompt = f"""你是一位资深简历顾问。请基于用户的底版简历和目标岗位要求，生成一份针对性简历，并分析匹配度和调整策略。

底版简历（项目已压缩为名称列表，原始项目数据在生成后直接复用）：
<user_content>
{resume_compact}
</user_content>

目标岗位：
<user_content>
{jd_info}
</user_content>

要求：
1. 调整简历简介(summary)，突出与目标岗位匹配的方面
2. 重新组织工作经历(experience)，强调与岗位相关的职责和成果
3. 技能(skills)按岗位需求排序，把匹配的技能放在前面，格式为字符串数组（不要用对象或字典）
4. 从项目名称列表中选出与目标岗位最相关的项目(selected_projects)，按相关度从高到低排序，最多8个。只返回项目名称字符串数组
5. 评估简历与岗位的匹配度(grade: A/B/C/D)，给出具体的技能匹配和经验匹配分析
6. 分析你做了哪些关键调整(adjustments)，每个调整说明领域、动作、原因和侧重点

请返回JSON：
{{
    "content": {{
        "summary": "针对该岗位调整后的个人简介",
        "experience": [],
        "skills": ["技能1", "技能2"],
        "education": []
    }},
    "selected_projects": ["最相关的项目名称1", "项目名称2"],
    "match": {{
        "grade": "A/B/C/D",
        "skill_match": {{"matched": ["匹配的技能"], "missing": ["缺失的技能"]}},
        "experience_match": {{"relevant": ["相关经历"], "gaps": ["经验缺口"]}},
        "strengths": ["优势1"],
        "risks": ["风险1"],
        "recommendation": "投递建议"
    }},
    "adjustment_report": {{
        "summary": "一句话调整策略",
        "adjustments": [
            {{
                "area": "调整领域",
                "action": "具体调整",
                "reason": "调整原因",
                "emphasis": "突出/弱化内容"
            }}
        ],
        "packaging": "包装策略",
        "risk_note": "风险提示"
    }}
}}"""

        schema = {
            "content": {"summary": "", "experience": [], "skills": [], "education": []},
            "selected_projects": [],
            "match": {"grade": "A", "skill_match": {}, "experience_match": {}, "strengths": [], "risks": [], "recommendation": ""},
            "adjustment_report": {"summary": "", "adjustments": [], "packaging": "", "risk_note": ""},
        }

        result = await llm_client.structured_output(gen_prompt, schema, timeout=180.0)

        targeted_content = result.get("content", {})
        if isinstance(targeted_content.get("skills"), dict):
            flat = []
            for v in targeted_content["skills"].values():
                if isinstance(v, list):
                    flat.extend(v)
            targeted_content["skills"] = flat
        targeted_content.setdefault("skills", [])

        # Filter projects by LLM selection, inject only relevant ones
        selected_names = result.get("selected_projects", [])
        targeted_content["projects"] = filter_projects_by_selection(selected_names, projects)

        # Preserve personal_info from base resume so exports show real name
        if resume_data.get("personal_info"):
            targeted_content["personal_info"] = resume_data["personal_info"]

        match_result = result.get("match", {"grade": "C", "recommendation": "分析失败"})
        adjustment_report = result.get("adjustment_report", {"summary": "调整分析生成失败", "adjustments": [], "packaging": "", "risk_note": ""})

        async with AsyncSessionLocal() as db:
            r = await db.execute(select(TargetedResume).where(TargetedResume.id == targeted_id))
            targeted = r.scalar_one_or_none()
            if not targeted:
                return
            targeted.content = json.dumps(targeted_content, ensure_ascii=False)
            targeted.match_result = json.dumps(match_result, ensure_ascii=False)
            targeted.adjustment_report = json.dumps(adjustment_report, ensure_ascii=False)
            targeted.generation_status = "success"
            targeted.generation_error = None
            targeted.updated_at = datetime.now()
            await db.commit()

    except Exception as e:
        import logging
        logging.getLogger().error(f"Targeted resume generation failed: {e}")
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(TargetedResume).where(TargetedResume.id == targeted_id))
            targeted = result.scalar_one_or_none()
            if targeted:
                targeted.generation_status = "failed"
                targeted.generation_error = str(e)[:200] if not isinstance(e, (ValueError, KeyError, AttributeError)) else "生成失败，请重试"
                targeted.updated_at = datetime.now()
                await db.commit()


@router.post("/targeted/generate")
async def generate_targeted_resume(
    req: GenerateTargetedRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    jd_result = await db.execute(
        select(JobDescription).where(
            JobDescription.id == req.jd_id,
            JobDescription.user_id == user_id,
        )
    )
    jd = jd_result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="JD不存在")

    base_result = await db.execute(
        select(BaseResume).where(BaseResume.user_id == user_id)
    )
    base = base_result.scalar_one_or_none()
    if not base or base.generation_status != "success":
        raise HTTPException(status_code=400, detail="请先生成底版简历")

    name = html.escape(f"{jd.title} - 定向简历"[:100])
    targeted = TargetedResume(
        id=str(uuid.uuid4()),
        user_id=user_id,
        jd_id=req.jd_id,
        name=name,
        content="{}",
        generation_status="pending",
        version=1,
    )
    db.add(targeted)
    await db.flush()

    tid = targeted.id

    task = asyncio.create_task(_generate_targeted_task(tid, user_id, req.jd_id))
    task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)

    return {
        "id": tid,
        "name": name,
        "generation_status": "pending",
        "jd_title": jd.title,
    }


@router.get("/targeted")
async def list_targeted_resumes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    offset = (page - 1) * page_size

    count = await db.execute(
        select(func.count()).select_from(TargetedResume).where(TargetedResume.user_id == user_id)
    )
    total = count.scalar() or 0

    result = await db.execute(
        select(TargetedResume)
        .where(TargetedResume.user_id == user_id)
        .order_by(TargetedResume.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    resumes = result.scalars().all()

    jd_ids = list(set(r.jd_id for r in resumes))
    jd_map = {}
    if jd_ids:
        jd_result = await db.execute(
            select(JobDescription.id, JobDescription.title).where(JobDescription.id.in_(jd_ids))
        )
        jd_map = dict(jd_result.all())

    items = []
    for r in resumes:
        jd_title = jd_map.get(r.jd_id, "未知岗位")
        match = {}
        try:
            match = json.loads(r.match_result) if r.match_result else {}
        except (json.JSONDecodeError, TypeError):
            pass
        adj = {}
        try:
            adj = json.loads(r.adjustment_report) if r.adjustment_report else {}
        except (json.JSONDecodeError, TypeError):
            pass
        items.append({
            "id": r.id,
            "name": r.name,
            "jd_id": r.jd_id,
            "jd_title": jd_title,
            "grade": match.get("grade", ""),
            "recommendation": match.get("recommendation", ""),
            "adjustment_report": adj if adj else None,
            "version": r.version,
            "generation_status": r.generation_status or "success",
            "generation_error": r.generation_error,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
        })
    return {"total": total, "page": page, "page_size": page_size, "total_pages": math.ceil(total / page_size) if total > 0 else 1, "items": items}


@router.get("/targeted/{resume_id}")
async def get_targeted_resume(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    r = await get_owned(TargetedResume, resume_id, user_id, db)
    match = {}
    try:
        match = json.loads(r.match_result) if r.match_result else {}
    except (json.JSONDecodeError, TypeError):
        pass
    adj = {}
    try:
        adj = json.loads(r.adjustment_report) if r.adjustment_report else {}
    except (json.JSONDecodeError, TypeError):
        pass
    return {
        "id": r.id,
        "name": r.name,
        "jd_id": r.jd_id,
        "content": json.loads(r.content) if r.content else None,
        "match_result": match,
        "adjustment_report": adj if adj else None,
        "version": r.version,
        "generation_status": r.generation_status or "success",
        "generation_error": r.generation_error,
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat(),
    }


@router.put("/targeted/{resume_id}")
async def update_targeted_resume(
    resume_id: str,
    req: UpdateResumeContent,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    r = await get_owned(TargetedResume, resume_id, user_id, db)
    try:
        json.loads(req.content)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail="无效的JSON内容")
    r.content = req.content
    r.version += 1
    r.updated_at = datetime.now()
    await db.flush()
    return {"id": r.id, "version": r.version}


@router.delete("/targeted/{resume_id}")
async def delete_targeted_resume(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    r = await get_owned(TargetedResume, resume_id, user_id, db)
    await db.delete(r)
    await db.flush()
    return {"status": "deleted"}


@router.get("/targeted/{resume_id}/export/{format}")
async def export_targeted_resume(
    resume_id: str,
    format: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    if format not in ("pdf", "docx", "txt"):
        raise HTTPException(status_code=400, detail="格式仅支持 pdf/docx/txt")

    r = await get_owned(TargetedResume, resume_id, user_id, db)

    try:
        content = json.loads(r.content)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=500, detail="简历内容损坏")

    safe_name = sanitize_filename(r.name or "resume")
    unique_name = f"{user_id[:8]}_{resume_id[:8]}_{safe_name}"

    if format == "pdf":
        from services.exporter.pdf_exporter import export_to_pdf
        from fastapi.responses import FileResponse
        from starlette.background import BackgroundTask
        file_path = await export_to_pdf(content, "simple", unique_name)
        return FileResponse(path=file_path, filename=f"{safe_name}.pdf", media_type="application/pdf", background=BackgroundTask(_remove_file, file_path))
    elif format == "docx":
        from services.exporter.docx_exporter import export_to_docx
        from fastapi.responses import FileResponse
        from starlette.background import BackgroundTask
        file_path = await export_to_docx(content, unique_name)
        return FileResponse(path=file_path, filename=f"{safe_name}.docx", media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", background=BackgroundTask(_remove_file, file_path))
    else:
        from fastapi.responses import PlainTextResponse
        skills = content.get("skills") or []
        if isinstance(skills, dict):
            skills = [v for vals in skills.values() if isinstance(vals, list) for v in vals]
        txt = f"{r.name}\n\n"
        txt += f"简介\n{content.get('summary', '')}\n\n"
        txt += "项目经历\n"
        for p in content.get("projects", []):
            txt += f"- {p.get('name', '')}: {p.get('description', '') or p.get('situation', '')}\n"
        txt += f"\n技能\n{' | '.join(str(s) for s in skills)}\n"
        return PlainTextResponse(content=txt, media_type="text/plain; charset=utf-8")
