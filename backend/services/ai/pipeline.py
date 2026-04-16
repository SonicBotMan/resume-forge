"""AI pipeline service integrating all prompt modules."""

import json
import logging
from typing import Dict, Any, List, Optional

from services.ai.client import llm_client
from services.ai.prompts.merge import get_merge_prompt
from services.ai.prompts.rewrite import get_rewrite_prompt
from services.ai.prompts.generate import get_generate_prompt
from services.ai.prompts.jd_parse import get_jd_parse_prompt
from services.ai.prompts.ats_score import (
    get_ats_score_prompt,
    calculate_local_ats_score,
)
from services.ai.prompts.optimize import get_optimize_prompt

logger = logging.getLogger(__name__)


async def parse_jd(jd_text: str) -> Dict[str, Any]:
    """Parse a job description into structured data."""
    prompt = get_jd_parse_prompt(jd_text)
    schema = {
        "required_skills": [],
        "preferred_skills": [],
        "soft_skills": [],
        "seniority_level": "",
        "education_requirements": "",
        "experience_years": "",
        "industry_keywords": [],
        "role_summary": "",
        "hiring_motivation": "",
        "talent_focus": "",
        "special_barriers": [],
        "career_growth": "",
        "interview_focus": [],
        "salary_insight": "",
    }
    try:
        result = await llm_client.structured_output(prompt, schema)
        return result
    except Exception as e:
        logger.warning("parse_jd failed, using fallback: %s", e)
        return _fallback_jd_parse(jd_text)


async def score_ats(
    resume_text: str,
    jd_parsed: Dict[str, Any],
    use_llm: bool = True,
) -> Dict[str, Any]:
    """Calculate ATS score for a resume against a parsed JD.

    Args:
        resume_text: Full resume text.
        jd_parsed: Structured JD data from parse_jd().
        use_llm: If True, use LLM for deep analysis; otherwise local-only.

    Returns:
        ATS score result with breakdown.
    """
    local_score = calculate_local_ats_score(
        resume_text=resume_text,
        required_skills=jd_parsed.get("required_skills", []),
        preferred_skills=jd_parsed.get("preferred_skills", []),
        soft_skills=jd_parsed.get("soft_skills", []),
        industry_keywords=jd_parsed.get("industry_keywords", []),
    )

    if not use_llm:
        return local_score

    prompt = get_ats_score_prompt(jd_parsed, resume_text)
    schema = {
        "total_score": 0,
        "breakdown": {
            "required_skills": {"score": 0, "matched": [], "missing": []},
            "preferred_skills": {"score": 0, "matched": [], "missing": []},
            "soft_skills": {"score": 0, "matched": []},
            "keyword_density": {"score": 0, "density": 0},
            "quantification": {"score": 0, "examples": []},
        },
        "improvement_suggestions": [],
    }
    try:
        llm_result = await llm_client.structured_output(prompt, schema)
    except Exception as e:
        logger.warning("score_ats LLM failed, using local score: %s", e)
        return local_score

    # Cap all scores at 100 to prevent display overflow
    def cap_score(val):
        if isinstance(val, (int, float)):
            return max(0, min(100, int(val)))
        if isinstance(val, str):
            try:
                return max(0, min(100, int(float(val))))
            except (ValueError, TypeError):
                return 0
        return val

    llm_result["total_score"] = cap_score(llm_result.get("total_score", 0))
    for dim_key in [
        "required_skills",
        "preferred_skills",
        "soft_skills",
        "keyword_density",
        "quantification",
    ]:
        if dim_key in llm_result.get("breakdown", {}):
            dim = llm_result["breakdown"][dim_key]
            dim["score"] = cap_score(dim.get("score", 0))
            if "matched" in dim:
                dim["matched"] = dim["matched"][:20]
            if "missing" in dim:
                dim["missing"] = dim["missing"][:20]

    if "improvement_suggestions" in llm_result:
        llm_result["improvement_suggestions"] = llm_result["improvement_suggestions"][
            :5
        ]

    # Merge: prefer LLM result but keep local fallback values where LLM missed
    merged = llm_result
    merged["local_score"] = local_score["total_score"]
    return merged


async def optimize_project(
    project_text: str,
    jd_parsed: Dict[str, Any],
    num_versions: int = 3,
) -> Dict[str, Any]:
    """Generate multiple optimized versions of a project description."""
    jd_json = json.dumps(jd_parsed, ensure_ascii=False)
    prompt = get_optimize_prompt(jd_json, project_text, num_versions)
    schema = {
        "versions": [
            {
                "version_id": "",
                "style": "",
                "content": "",
                "ats_score_delta": "",
                "key_changes": [],
            }
        ]
    }
    try:
        result = await llm_client.structured_output(prompt, schema)
        return result
    except Exception as e:
        logger.warning("optimize_project failed, returning original: %s", e)
        return {
            "versions": [
                {
                    "version_id": "v1",
                    "style": "原文",
                    "content": project_text,
                    "ats_score_delta": "+0",
                    "key_changes": [],
                }
            ]
        }


async def merge_projects(
    source1: str,
    project1: str,
    source2: str,
    project2: str,
) -> Dict[str, Any]:
    """Merge two project descriptions about the same project."""
    prompt = get_merge_prompt(source1, project1, source2, project2)
    schema = {
        "name": "",
        "role": "",
        "time_range": {"start": "", "end": ""},
        "situation": "",
        "task": "",
        "action": "",
        "result": "",
    }
    try:
        result = await llm_client.structured_output(prompt, schema)
        return result
    except Exception as e:
        logger.warning("merge_projects failed, using naive merge: %s", e)
        return {
        }


async def rewrite_content(raw_description: str) -> str:
    """Rewrite raw description into professional resume language."""
    prompt = get_rewrite_prompt(raw_description)
    result = await llm_client.chat(prompt)
    if result.startswith("[AI Error"):
        return raw_description
    return result


async def generate_resume(
    projects: str,
    skills: str,
    achievements: str,
    jd_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a full resume from extracted data."""
    prompt = get_generate_prompt(projects, skills, achievements, jd_text=jd_text)
    schema = {
        "summary": "",
        "experience": [],
        "projects": [],
        "skills": [],
        "education": [],
    }
    try:
        result = await llm_client.structured_output(prompt, schema)
    except Exception as e:
        logger.warning("generate_resume failed, returning empty: %s", e)
        return {
        }
    # Ensure skills is always a list (LLM sometimes returns dict)
    if isinstance(result.get("skills"), dict):
        original = result["skills"]
        result["skills"] = []
        for v in original.values():
            if isinstance(v, list):
                result["skills"].extend(v)
            elif isinstance(v, str):
                result["skills"].append(v)
    return result


def _fallback_jd_parse(jd_text: str) -> Dict[str, Any]:
    """Minimal fallback JD parser when LLM is unavailable."""
    lines = jd_text.split("\n")
    words = jd_text.split()
    return {
        "required_skills": [],
        "preferred_skills": [],
        "soft_skills": [],
        "seniority_level": "mid",
        "education_requirements": "",
        "experience_years": "",
        "industry_keywords": [],
        "role_summary": lines[0][:100] if lines else "",
        "hiring_motivation": "",
        "talent_focus": "综合型（LLM不可用，使用默认值）",
        "special_barriers": [],
        "career_growth": "",
        "interview_focus": [],
        "salary_insight": "",
    }
