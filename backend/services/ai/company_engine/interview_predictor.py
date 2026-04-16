"""Interview question prediction based on resume, target company, and JD."""

import json
from typing import Any, Dict, List

from services.ai.client import llm_client
from services.ai.company_engine.company_profiles import get_profile


_INTERVIEW_PREDICT_PROMPT = """你是一位资深的面试官和职业辅导教练，精通 {company_name} 的面试流程和评估标准。

## 目标公司：{company_name}
## 公司领导力准则
{leadership_text}

## 候选人简历摘要
---
{resume_summary}
---

## 目标职位分析
{jd_summary}
---

## 任务
请预测 {company_name} 面试中可能问到的 **8** 个问题，涵盖以下类型：

### 行为类问题（behavioral）
- 基于公司领导力准则设计
- 使用 STAR 方法回答
- 针对简历中的经历提问

### 技术类问题（technical）
- 基于 JD 技术要求设计
- 涵盖系统设计、算法、架构等
- 结合简历中的技术栈深入提问

### 文化匹配类问题（cultural_fit）
- 考察与公司价值观的匹配度
- 针对简历中的团队协作经历
- 评估候选人是否认同公司文化

## 输出格式

严格返回以下 JSON（不要包含任何其他内容）：
{{
    "questions": [
        {{
            "question": "具体问题文本",
            "type": "behavioral",
            "principle": "{company_name}: 对应的领导力准则",
            "answer_framework": "STAR",
            "key_points": ["要点1", "要点2"],
            "difficulty": "medium"
        }},
        {{
            "question": "具体问题文本",
            "type": "technical",
            "focus": "系统设计",
            "key_points": ["要点1", "要点2"],
            "difficulty": "hard"
        }},
        {{
            "question": "具体问题文本",
            "type": "cultural_fit",
            "principle": "{company_name}: 文化价值观",
            "answer_framework": "叙事型",
            "key_points": ["要点1", "要点2"],
            "difficulty": "medium"
        }}
    ]
}}
"""


def _build_leadership_text(profile) -> str:
    if profile is None:
        return "通用面试标准"
    principles = profile.get("leadership_principles", [])
    return "\n".join(f"- {p}" for p in principles) if principles else "通用面试标准"


def _extract_resume_summary(resume: Dict[str, Any]) -> str:
    """Build a concise summary from structured resume data."""
    parts: List[str] = []

    if "summary" in resume and resume["summary"]:
        parts.append(f"个人简介: {resume['summary']}")

    skills = resume.get("skills", [])
    if skills:
        if isinstance(skills, list):
            parts.append(f"技能: {', '.join(str(s) for s in skills[:20])}")
        else:
            parts.append(f"技能: {skills}")

    projects = resume.get("projects", [])
    if projects:
        for p in projects[:5]:
            name = p.get("name", "") or p.get("项目", "")
            desc = p.get("description", "") or p.get("result", "") or p.get("结果", "")
            if name:
                parts.append(f"项目 {name}: {desc}")

    experience = resume.get("experience", [])
    if experience:
        for e in experience[:3]:
            company_name = e.get("company", "") or e.get("公司", "")
            role = e.get("role", "") or e.get("职位", "")
            if company_name or role:
                parts.append(f"经历: {company_name} - {role}")

    return "\n".join(parts) if parts else json.dumps(resume, ensure_ascii=False)[:500]


def _extract_jd_summary(jd: Dict[str, Any]) -> str:
    parts: List[str] = []
    if "role_summary" in jd and jd["role_summary"]:
        parts.append(f"岗位概述: {jd['role_summary']}")
    if "required_skills" in jd and jd["required_skills"]:
        parts.append(f"必备技能: {', '.join(jd['required_skills'])}")
    if "preferred_skills" in jd and jd["preferred_skills"]:
        parts.append(f"加分技能: {', '.join(jd['preferred_skills'])}")
    if "seniority_level" in jd:
        parts.append(f"级别: {jd['seniority_level']}")
    return "\n".join(parts) if parts else json.dumps(jd, ensure_ascii=False)[:500]


def _generate_local_questions(
    resume: Dict[str, Any],
    company: str,
    jd: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate basic interview questions locally when LLM is unavailable."""
    profile = get_profile(company)
    company_name = profile["name"] if profile else company
    principles = profile.get("leadership_principles", []) if profile else []

    questions: List[Dict[str, Any]] = []

    skills = jd.get("required_skills", [])
    if skills:
        top_skills = skills[:3]
        questions.append(
            {
                "question": f"请详细描述你使用 {'、'.join(top_skills)} 解决复杂问题的经历",
                "type": "technical",
                "focus": "技术深度",
                "key_points": top_skills,
                "difficulty": "medium",
            }
        )

    if principles:
        questions.append(
            {
                "question": f'描述一个体现 "{principles[0]}" 的经历',
                "type": "behavioral",
                "principle": f"{company_name}: {principles[0]}",
                "answer_framework": "STAR",
                "key_points": ["具体场景", "你的行动", "量化结果"],
                "difficulty": "medium",
            }
        )
        if len(principles) > 1:
            questions.append(
                {
                    "question": f'请举例说明你如何在工作中实践 "{principles[1]}"',
                    "type": "behavioral",
                    "principle": f"{company_name}: {principles[1]}",
                    "answer_framework": "STAR",
                    "key_points": ["挑战描述", "决策过程", "最终结果"],
                    "difficulty": "medium",
                }
            )

    questions.append(
        {
            "question": "描述一个你在团队中推动技术决策的经历",
            "type": "behavioral",
            "principle": f"{company_name}: 团队协作",
            "answer_framework": "STAR",
            "key_points": ["背景", "决策依据", "影响"],
            "difficulty": "medium",
        }
    )

    questions.append(
        {
            "question": "你如何处理项目中的技术债务？请举例说明",
            "type": "technical",
            "focus": "工程实践",
            "key_points": ["识别", "优先级", "实施"],
            "difficulty": "hard",
        }
    )

    questions.append(
        {
            "question": f"你为什么选择 {company_name}？你认为你能带来什么价值？",
            "type": "cultural_fit",
            "principle": f"{company_name}: 文化匹配",
            "answer_framework": "叙事型",
            "key_points": ["对公司了解", "价值对齐", "独特贡献"],
            "difficulty": "easy",
        }
    )

    return questions


async def predict_interview_questions(
    resume: Dict[str, Any],
    company: str,
    jd: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Predict interview questions tailored to the target company.

    Uses LLM for deep analysis, falls back to template-based generation.
    """
    profile = get_profile(company)
    company_name = profile["name"] if profile else company

    resume_summary = _extract_resume_summary(resume)
    jd_summary = _extract_jd_summary(jd)
    leadership_text = _build_leadership_text(profile) if profile else "通用面试标准"

    prompt = _INTERVIEW_PREDICT_PROMPT.format(
        company_name=company_name,
        leadership_text=leadership_text,
        resume_summary=resume_summary,
        jd_summary=jd_summary,
    )

    schema = {
        "questions": [
            {
                "question": "",
                "type": "",
                "principle": "",
                "answer_framework": "",
                "key_points": [],
                "difficulty": "",
            }
        ]
    }

    result = await llm_client.structured_output(prompt, schema)

    if "error" in result or "questions" not in result:
        return _generate_local_questions(resume, company, jd)

    return result["questions"]
