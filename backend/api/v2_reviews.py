import json
import math
import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from api.v2_resumes import filter_projects_by_selection

from db import get_db
from models.review_session import ReviewSession
from models.base_resume import BaseResume
from models.targeted_resume import TargetedResume
from models.job_description import JobDescription
from api.auth import get_current_user_id
from api.deps import get_owned
from services.ai.client import llm_client
from services.ai.prompts.review import get_role_prompt, get_synthesis_prompt

router = APIRouter()

ROLES = ["hr", "headhunter", "interviewer", "manager", "expert"]


class CreateReviewRequest(BaseModel):
    resume_id: str
    resume_type: str  # "base" or "targeted"


async def _run_review(review_id: str, resume_content: str, jd_text: str = None):
    from db import AsyncSessionLocal

    async def review_role(role: str) -> dict:
        prompt = get_role_prompt(role, resume_content, jd_text)
        schema = {"role": "", "problems": [], "suggestions": [], "score_impact": "", "key_insight": ""}
        try:
            result = await llm_client.structured_output(prompt, schema)
            return result
        except Exception as e:
            return {"role": role, "problems": [str(e)], "suggestions": [], "score_impact": "neutral", "key_insight": "评审失败"}

    role_results = await asyncio.gather(*[review_role(r) for r in ROLES])

    role_map = {}
    for r, result in zip(ROLES, role_results):
        role_map[r] = json.dumps(result, ensure_ascii=False)

    syn_prompt = get_synthesis_prompt(role_map, resume_content)
    syn_schema = {
        "overall_assessment": "",
        "critical_fixes": [],
        "recommended_improvements": [],
        "resume_revisions": {},
        "interview_plan": {},
    }
    try:
        synthesis = await llm_client.structured_output(syn_prompt, syn_schema)
    except Exception:
        synthesis = {"overall_assessment": "综合分析失败", "critical_fixes": [], "recommended_improvements": []}

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ReviewSession).where(ReviewSession.id == review_id)
        )
        review = result.scalar_one_or_none()
        if not review:
            return

        review.hr_review = role_map.get("hr")
        review.headhunter_review = role_map.get("headhunter")
        review.interviewer_review = role_map.get("interviewer")
        review.manager_review = role_map.get("manager")
        review.expert_review = role_map.get("expert")
        review.synthesis = json.dumps(synthesis, ensure_ascii=False)

        interview_plan = synthesis.get("interview_plan", {})
        review.interview_plan = json.dumps(interview_plan, ensure_ascii=False) if interview_plan else None
        review.status = "completed"
        review.updated_at = datetime.now()
        await db.commit()


@router.post("")
async def create_review(
    req: CreateReviewRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    content_str = None
    jd_text = None

    if req.resume_type == "base":
        result = await db.execute(
            select(BaseResume).where(BaseResume.id == req.resume_id, BaseResume.user_id == user_id)
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise HTTPException(status_code=404, detail="底版简历不存在")
        content_str = resume.content
    elif req.resume_type == "targeted":
        result = await db.execute(
            select(TargetedResume).where(TargetedResume.id == req.resume_id, TargetedResume.user_id == user_id)
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise HTTPException(status_code=404, detail="定向简历不存在")
        content_str = resume.content

        jd_result = await db.execute(
            select(JobDescription).where(JobDescription.id == resume.jd_id)
        )
        jd = jd_result.scalar_one_or_none()
        if jd:
            jd_text = jd.jd_text
    else:
        raise HTTPException(status_code=400, detail="resume_type 必须是 base 或 targeted")

    review = ReviewSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        resume_id=req.resume_id,
        resume_type=req.resume_type,
        status="running",
    )
    db.add(review)
    await db.flush()

    task = asyncio.create_task(_run_review(review.id, content_str, jd_text))
    task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)

    return {"id": review.id, "status": "running"}


@router.get("")
async def list_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    offset = (page - 1) * page_size

    count = await db.execute(
        select(func.count()).select_from(ReviewSession).where(ReviewSession.user_id == user_id)
    )
    total = count.scalar() or 0

    result = await db.execute(
        select(ReviewSession)
        .where(ReviewSession.user_id == user_id)
        .order_by(ReviewSession.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    reviews = result.scalars().all()

    items = []
    for r in reviews:
        item = {
            "id": r.id,
            "resume_id": r.resume_id,
            "resume_type": r.resume_type,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
            "resume_name": None,
            "jd_title": None,
        }
        if r.resume_type == "targeted":
            tr = await db.execute(select(TargetedResume).where(TargetedResume.id == r.resume_id))
            targeted = tr.scalar_one_or_none()
            if targeted:
                item["resume_name"] = targeted.name
                jd_r = await db.execute(select(JobDescription).where(JobDescription.id == targeted.jd_id))
                jd = jd_r.scalar_one_or_none()
                if jd:
                    item["jd_title"] = jd.title
        elif r.resume_type == "base":
            br = await db.execute(select(BaseResume).where(BaseResume.id == r.resume_id))
            base = br.scalar_one_or_none()
            if base:
                item["resume_name"] = "底版简历"
        items.append(item)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 1,
        "items": items,
    }


@router.get("/{review_id}")
async def get_review(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    review = await get_owned(ReviewSession, review_id, user_id, db)

    def safe_parse(s):
        try:
            return json.loads(s) if s else None
        except (json.JSONDecodeError, TypeError):
            return None

    return {
        "id": review.id,
        "resume_id": review.resume_id,
        "resume_type": review.resume_type,
        "status": review.status,
        "hr_review": safe_parse(review.hr_review),
        "headhunter_review": safe_parse(review.headhunter_review),
        "interviewer_review": safe_parse(review.interviewer_review),
        "manager_review": safe_parse(review.manager_review),
        "expert_review": safe_parse(review.expert_review),
        "synthesis": safe_parse(review.synthesis),
        "interview_plan": safe_parse(review.interview_plan),
        "created_at": review.created_at.isoformat(),
        "updated_at": review.updated_at.isoformat(),
    }


@router.get("/{review_id}/status")
async def get_review_status(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    result = await db.execute(
        select(ReviewSession).where(ReviewSession.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="评审不存在")
    if review.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问")
    return {"status": review.status, "updated_at": review.updated_at.isoformat()}


@router.delete("/{review_id}")
async def delete_review(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    review = await get_owned(ReviewSession, review_id, user_id, db)
    await db.delete(review)
    await db.commit()
    return {"detail": "评审已删除"}


@router.post("/{review_id}/regenerate-resume")
async def regenerate_resume_from_review(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    import html as html_mod
    from services.ai.client import llm_client

    review = await get_owned(ReviewSession, review_id, user_id, db)
    if review.status != "completed":
        raise HTTPException(status_code=400, detail="评审尚未完成")
    if review.resume_type != "targeted":
        raise HTTPException(status_code=400, detail="仅支持基于定向简历的评审重生成")

    def safe_parse(s):
        try:
            return json.loads(s) if s else None
        except (json.JSONDecodeError, TypeError):
            return None

    synthesis = safe_parse(review.synthesis)
    if not synthesis or not synthesis.get("resume_revisions"):
        raise HTTPException(status_code=400, detail="评审结果中无简历修改建议")

    tr_result = await db.execute(select(TargetedResume).where(TargetedResume.id == review.resume_id))
    targeted = tr_result.scalar_one_or_none()
    if not targeted:
        raise HTTPException(status_code=404, detail="关联的定向简历不存在")

    jd_result = await db.execute(select(JobDescription).where(JobDescription.id == targeted.jd_id))
    jd = jd_result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="关联的岗位描述不存在")

    base_result = await db.execute(select(BaseResume).where(BaseResume.user_id == user_id))
    base = base_result.scalar_one_or_none()
    if not base:
        raise HTTPException(status_code=400, detail="底版简历不存在")

    current_content = safe_parse(targeted.content) or {}
    revisions = synthesis["resume_revisions"]
    resume_data = json.loads(base.content)

    projects = resume_data.get("projects", [])
    compressed = {}
    if resume_data.get("personal_info"):
        compressed["personal_info"] = resume_data["personal_info"]
    compressed["summary"] = resume_data.get("summary", "")
    compressed["experience"] = resume_data.get("experience", [])
    compressed["education"] = resume_data.get("education", [])
    compressed["skills"] = resume_data.get("skills", [])
    compressed["projects_count"] = len(projects)
    compressed["projects_sample"] = [
        {"name": p.get("name"), "role": p.get("role"), "period": f"{p.get('start_date','')}~{p.get('end_date','')}"}
        for p in projects[:20]
    ]
    resume_compact = json.dumps(compressed, ensure_ascii=False)

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

    revision_prompt = f"""你是一位资深简历顾问。之前已为用户生成了一份针对目标岗位的定向简历，并进行了多角色评审。
现在请根据评审结果中的修改建议，重新生成一份更优的定向简历。

底版简历核心数据：
<user_content>
{resume_compact}
</user_content>

目标岗位：
<user_content>
{jd_info}
</user_content>

当前定向简历的简介：
<user_content>
{json.dumps(current_content.get("summary", ""), ensure_ascii=False)}
</user_content>

评审修改建议（必须全部落实）：
<user_content>
- 建议的新简介(summary): {json.dumps(revisions.get("summary", ""), ensure_ascii=False)}
- 必须增加的内容(key_additions): {json.dumps(revisions.get("key_additions", []), ensure_ascii=False)}
- 必须移除/弱化的内容(key_removals): {json.dumps(revisions.get("key_removals", []), ensure_ascii=False)}
- 语调调整(tone_adjustment): {json.dumps(revisions.get("tone_adjustment", ""), ensure_ascii=False)}
</user_content>

综合评审的其他建议：
<user_content>
关键修复: {json.dumps(synthesis.get("critical_fixes", []), ensure_ascii=False)}
改进建议: {json.dumps(synthesis.get("recommended_improvements", []), ensure_ascii=False)}
</user_content>

要求：
1. 严格按照评审建议修改简历，特别是 summary、key_additions、key_removals、tone_adjustment
2. 技能(skills)格式为字符串数组
3. 从底版简历的项目名称列表中选出与目标岗位最相关的项目(selected_projects)，按相关度从高到低排序，最多8个
4. 返回调整说明，解释相比之前版本做了哪些具体改动

请返回JSON：
{{
    "content": {{
        "summary": "按评审建议修改后的个人简介",
        "experience": [],
        "skills": ["技能1", "技能2"],
        "education": []
    }},
    "selected_projects": ["最相关的项目名称1", "项目名称2"],
    "changes": [
        {{"area": "修改领域", "before": "修改前", "after": "修改后", "reason": "评审建议原因"}}
    ]
}}"""

    schema = {
        "content": {"summary": "", "experience": [], "skills": [], "education": []},
        "selected_projects": [],
        "changes": [],
    }

    result = await llm_client.structured_output(revision_prompt, schema, timeout=180.0)

    new_content = result.get("content", {})
    if isinstance(new_content.get("skills"), dict):
        flat = []
        for v in new_content["skills"].values():
            if isinstance(v, list):
                flat.extend(v)
        new_content["skills"] = flat
    new_content.setdefault("skills", [])

    selected_names = result.get("selected_projects", [])
    new_content["projects"] = filter_projects_by_selection(selected_names, projects)

    if resume_data.get("personal_info"):
        new_content["personal_info"] = resume_data["personal_info"]

    changes = result.get("changes", [])

    new_targeted = TargetedResume(
        id=str(uuid.uuid4()),
        user_id=user_id,
        jd_id=targeted.jd_id,
        name=html_mod.escape(f"{jd.title} - 定向简历(v2)"[:100]),
        content=json.dumps(new_content, ensure_ascii=False),
        match_result=targeted.match_result,
        generation_status="success",
        version=(targeted.version or 1) + 1,
    )
    db.add(new_targeted)
    await db.flush()

    return {
        "id": new_targeted.id,
        "name": new_targeted.name,
        "jd_title": jd.title,
        "generation_status": "success",
        "changes": changes,
    }
