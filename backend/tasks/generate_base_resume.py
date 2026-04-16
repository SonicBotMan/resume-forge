import json
import uuid
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import AsyncSessionLocal
from models.base_resume import BaseResume
from models.material_analysis import MaterialAnalysis
from services.ai.client import llm_client

logger = logging.getLogger(__name__)


def _merge_analyses(analyses: list[MaterialAnalysis]) -> dict:
    all_projects = []
    all_skills = []
    all_achievements = []
    all_education = []
    all_experience = []
    all_personal_info = []
    all_summaries = []

    for a in analyses:
        if a.summary:
            all_summaries.append(a.summary)
        if a.projects_json:
            all_projects.extend(json.loads(a.projects_json))
        if a.skills_json:
            all_skills.extend(json.loads(a.skills_json))
        if a.achievements_json:
            all_achievements.extend(json.loads(a.achievements_json))
        if a.education_json:
            all_education.extend(json.loads(a.education_json))
        if a.experience_json:
            all_experience.extend(json.loads(a.experience_json))
        if a.raw_chunks_json:
            for chunk in json.loads(a.raw_chunks_json):
                content = chunk.get("content", "")
                lower = content.lower()
                if any(kw in lower for kw in ["姓名", "手机", "电话", "邮箱", "email", "电话", "出生", "现居", "地址"]):
                    all_personal_info.append(content[:800])

    seen = set()
    deduped_skills = []
    for s in all_skills:
        name = str(s.get("name", "")).strip()
        if not name:
            continue
        key = name.lower().replace(" ", "").replace("-", "").replace("_", "")
        if key not in seen:
            seen.add(key)
            deduped_skills.append(name)

    seen_exp = set()
    deduped_experience = []
    for e in all_experience:
        company = str(e.get("company", "")).strip()
        period = str(e.get("period", "")).strip()
        position = str(e.get("position", "")).strip()
        key = f"{company}|{period}|{position}".lower()
        if key not in seen_exp and company:
            seen_exp.add(key)
            deduped_experience.append(e)
        elif key in seen_exp:
            for existing in deduped_experience:
                e_company = str(existing.get("company", "")).strip()
                e_period = str(existing.get("period", "")).strip()
                if e_company == company and e_period == period:
                    existing_highlights = existing.get("highlights", [])
                    new_highlights = e.get("highlights", [])
                    if isinstance(existing_highlights, list) and isinstance(new_highlights, list):
                        merged = list(dict.fromkeys(existing_highlights + new_highlights))
                        existing["highlights"] = merged
                    new_resp = e.get("responsibilities", [])
                    if new_resp and not existing.get("responsibilities"):
                        existing["responsibilities"] = new_resp
                    break

    seen_proj = set()
    deduped_projects = []
    for p in all_projects:
        name = str(p.get("name", "")).strip()
        if not name:
            continue
        key = name.lower().replace(" ", "")
        if key not in seen_proj:
            seen_proj.add(key)
            deduped_projects.append(p)
        else:
            for existing in deduped_projects:
                if str(existing.get("name", "")).strip().lower().replace(" ", "") == key:
                    for field in ["action", "result", "situation", "task", "description", "role", "start_date", "end_date"]:
                        if p.get(field) and not existing.get(field):
                            existing[field] = p[field]
                    break

    seen_edu = set()
    deduped_education = []
    for e in all_education:
        school = str(e.get("school", e.get("name", ""))).strip()
        if not school:
            continue
        key = school.lower()
        if key not in seen_edu:
            seen_edu.add(key)
            deduped_education.append(e)

    seen_ach = set()
    deduped_achievements = []
    for a in all_achievements:
        desc = str(a.get("description", str(a))).strip()
        if not desc:
            continue
        key = desc[:50].lower()
        if key not in seen_ach:
            seen_ach.add(key)
            deduped_achievements.append(a)

    return {
        "personal_info_hints": all_personal_info,
        "summaries": all_summaries,
        "projects": deduped_projects,
        "skills": deduped_skills,
        "achievements": deduped_achievements,
        "education": deduped_education,
        "experience": deduped_experience,
    }


async def generate_base_resume_task(user_id: str):
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(MaterialAnalysis).where(
                    MaterialAnalysis.user_id == user_id
                )
            )
            analyses = result.scalars().all()

            if not analyses:
                await _update_status(db, user_id, "failed", "请先分析至少一个资料")
                return

            merged = _merge_analyses(analyses)

            has_data = any([
                merged["projects"],
                merged["skills"],
                merged["achievements"],
                merged["education"],
                merged["experience"],
            ])
            if not has_data:
                await _update_status(db, user_id, "failed", "分析数据不足，请上传包含更详细工作经历的资料")
                return

            await _update_status(db, user_id, "generating")

        projects_compact = []
        for p in merged["projects"]:
            entry = {"项目": p.get("name", "")}
            if p.get("role"): entry["角色"] = p["role"]
            if p.get("start_date"): entry["时间"] = f"{p.get('start_date', '')}-{p.get('end_date', '至今')}"
            fields = {"背景": p.get("situation"), "任务": p.get("task"), "行动": p.get("action"), "成果": p.get("result"), "描述": p.get("description")}
            for k, v in fields.items():
                if v: entry[k] = v
            projects_compact.append(entry)

        exp_compact = []
        for e in merged["experience"]:
            entry = {"公司": e.get("company", ""), "职位": e.get("position", ""), "部门": e.get("department", ""), "时间": e.get("period", "")}
            if e.get("responsibilities"): entry["职责"] = e["responsibilities"]
            if e.get("highlights"): entry["亮点"] = e["highlights"]
            exp_compact.append(entry)

        edu_compact = []
        for e in merged["education"]:
            entry = {"学校": e.get("school", e.get("name", ""))}
            if e.get("major"): entry["专业"] = e["major"]
            if e.get("degree"): entry["学历"] = e["degree"]
            if e.get("period"): entry["时间"] = e["period"]
            edu_compact.append(entry)

        ach_compact = [a.get("description", str(a)) for a in merged["achievements"]]

        projects_brief = []
        for p in merged["projects"]:
            entry = p.get("name", "")
            if p.get("role"): entry += f"（{p['role']}）"
            if p.get("start_date"): entry += f" [{p.get('start_date','')}-{p.get('end_date','')}]"
            has_star = any(p.get(f) for f in ["situation", "task", "action", "result", "description"])
            entry += " ★" if has_star else " ☆"
            projects_brief.append(entry)

        aggregate_prompt = f"""你是资深简历顾问。基于用户{len(analyses)}份资料中提取的数据，生成基础简历的核心部分。

个人线索：{json.dumps(merged["personal_info_hints"], ensure_ascii=False) if merged["personal_info_hints"] else "（无）"}
资料概述：{json.dumps(merged["summaries"], ensure_ascii=False)}

工作经历（{len(exp_compact)}段）：
{json.dumps(exp_compact, ensure_ascii=False, indent=2)}

项目列表（{len(projects_brief)}个，★=有详情 ☆=需推断）：
{json.dumps(projects_brief, ensure_ascii=False)}

技能（{len(merged["skills"])}项）：{json.dumps(merged["skills"][:60], ensure_ascii=False)}
工作成果（{len(ach_compact)}条）：{json.dumps(ach_compact[:20], ensure_ascii=False)}
教育背景：{json.dumps(edu_compact, ensure_ascii=False) if edu_compact else "（推断）"}

要求：
1. 从项目时间线推断补充缺失的工作经历
2. 每段经历2-4条量化亮点，2-3条核心职责
3. 技能按类型分3组
4. 100-150字个人简介
5. 不需要输出projects，我已有原始数据

返回JSON（不含projects）：
{{"personal_info":{{"name":"","phone":"","email":"","location":"","birth_year":""}},"summary":"","experience":[{{"company":"","position":"","department":"","period":"","responsibilities":[],"highlights":[]}}],"skills":{{"专业技能":[],"工具与平台":[],"软技能":[]}},"education":[{{"school":"","major":"","degree":"","period":""}}],"career_highlights":[]}}"""

        aggregate_schema = {
            "personal_info": {"name": "", "phone": "", "email": "", "location": "", "birth_year": ""},
            "summary": "",
            "experience": [],
            "skills": {},
            "education": [],
            "career_highlights": [],
        }

        try:
            generated = await llm_client.structured_output(aggregate_prompt, aggregate_schema)
        except Exception as e:
            async with AsyncSessionLocal() as db:
                await _update_status(db, user_id, "failed", f"简历生成失败: {str(e)}")
            return

        if isinstance(generated.get("skills"), dict):
            flat = []
            for v in generated["skills"].values():
                if isinstance(v, list):
                    flat.extend(v)
            generated["skills"] = flat
        generated.setdefault("skills", [])

        # Projects were excluded from LLM to save tokens; inject deduped originals
        generated["projects"] = merged["projects"]

        source_ids = json.dumps([a.material_id for a in analyses])
        content_str = json.dumps(generated, ensure_ascii=False)

        async with AsyncSessionLocal() as db:
            existing = await db.execute(
                select(BaseResume).where(BaseResume.user_id == user_id)
            )
            base = existing.scalar_one_or_none()

            if base:
                base.content = content_str
                base.source_material_ids = source_ids
                base.version += 1
                base.generation_status = "success"
                base.generation_error = None
                base.updated_at = datetime.now()
            else:
                base = BaseResume(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    content=content_str,
                    version=1,
                    source_material_ids=source_ids,
                    generation_status="success",
                )
                db.add(base)

            await db.commit()

    except Exception as e:
        logger.error(f"Base resume generation failed for user {user_id}: {e}", exc_info=True)
        try:
            async with AsyncSessionLocal() as db:
                await _update_status(db, user_id, "failed", str(e))
        except Exception:
            logger.error(f"Failed to update error status for user {user_id}")


async def _update_status(db: AsyncSession, user_id: str, status: str, error: str = None):
    existing = await db.execute(
        select(BaseResume).where(BaseResume.user_id == user_id)
    )
    base = existing.scalar_one_or_none()

    if base:
        base.generation_status = status
        base.generation_error = error
        if status == "generating":
            base.content = None
        base.updated_at = datetime.now()
    else:
        base = BaseResume(
            id=str(uuid.uuid4()),
            user_id=user_id,
            version=0,
            generation_status=status,
            generation_error=error,
        )
        db.add(base)

    await db.commit()
