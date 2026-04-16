"""Company-aware JD parsing with leadership alignment scoring."""

import re
from typing import Any, Dict, List

from services.ai.client import llm_client
from services.ai.company_engine.company_profiles import get_profile

_LEADERSHIP_KEYWORDS: Dict[str, List[str]] = {
    "customer_obsession": [
        "customer",
        "user experience",
        "用户",
        "客户",
        "client",
        "satisfaction",
        "NPS",
        "CSAT",
    ],
    "ownership": [
        "ownership",
        "own",
        "accountable",
        "responsible",
        "负责",
        "主导",
        "承担",
        "end-to-end",
    ],
    "bias_for_action": [
        "fast",
        "quick",
        "agile",
        "iterate",
        "rapid",
        "快速",
        "敏捷",
        "迭代",
        "deadline",
    ],
    "think_big": [
        "vision",
        "strategy",
        "roadmap",
        "long-term",
        "愿景",
        "战略",
        "规划",
        "长期",
    ],
    "dive_deep": [
        "data",
        "analysis",
        "investigate",
        "root cause",
        "数据",
        "分析",
        "深入",
        "排查",
    ],
    "invent_and_simplify": [
        "innovate",
        "simplify",
        "automate",
        "efficiency",
        "创新",
        "简化",
        "自动化",
        "效率",
    ],
    "deliver_results": [
        "deliver",
        "launch",
        "release",
        "impact",
        "交付",
        "上线",
        "发布",
        "成果",
    ],
}

JD_PARSE_WITH_CONTEXT_PROMPT = """你是一位资深的招聘分析专家，擅长针对特定公司的文化和价值观分析职位描述。

## 目标公司：{company_name}
## 公司核心价值观
{leadership_text}

## 职位描述
---
{jd_text}
---

## 分析要求

### 1. 基础信息提取
- **required_skills**: 必备硬技能（编程语言、框架、工具、证书等）
- **preferred_skills**: 加分技能
- **soft_skills**: 软性要求

### 2. 公司文化匹配分析
根据目标公司的领导力准则和价值观，分析该职位对以下能力的重视程度（0.0-1.0）：
{principles_json}

### 3. 风险点识别（red_flags）
列出候选人可能因为什么不足而被淘汰

### 4. 优化建议（suggestions）
针对目标公司给出简历优化建议

## 输出格式

严格返回以下 JSON（不要包含任何其他内容）：
{{
    "company": "{company_key}",
    "required_skills": ["技能1"],
    "preferred_skills": ["技能1"],
    "soft_skills": ["技能1"],
    "seniority_level": "mid",
    "education_requirements": "",
    "experience_years": "",
    "industry_keywords": [],
    "role_summary": "",
    "hiring_motivation": "",
    "leadership_alignment": {{
        "customer_obsession": 0.5,
        "ownership": 0.5,
        "bias_for_action": 0.5,
        "think_big": 0.5,
        "dive_deep": 0.5,
        "invent_and_simplify": 0.5,
        "deliver_results": 0.5
    }},
    "red_flags": [],
    "suggestions": []
}}
"""


def _score_leadership_alignment(jd_text: str) -> Dict[str, float]:
    """Locally estimate leadership principle alignment from JD text."""
    jd_lower = jd_text.lower()
    scores: Dict[str, float] = {}
    for principle, keywords in _LEADERSHIP_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw.lower() in jd_lower)
        scores[principle] = min(round(hits / max(len(keywords) * 0.3, 1), 2), 1.0)
    return scores


def _build_leadership_text(profile: Dict[str, Any]) -> str:
    principles = profile.get("leadership_principles", [])
    return "\n".join(f"- {p}" for p in principles)


def _build_principles_json() -> str:
    keys = list(_LEADERSHIP_KEYWORDS.keys())
    inner = ",\n        ".join(f'"{k}": 0.0' for k in keys)
    return "{{\n        " + inner + "\n    }}"


async def parse_jd_with_company_context(
    jd_text: str,
    company: str,
) -> Dict[str, Any]:
    """Parse JD with company-specific cultural context via LLM.

    Falls back to local analysis when LLM is unavailable.
    """
    profile = get_profile(company)

    if profile is None:
        return await _parse_generic(jd_text, company)

    company_name = profile["name"]
    company_key = company.strip().lower()
    leadership_text = _build_leadership_text(profile)
    principles_json = _build_principles_json()

    prompt = JD_PARSE_WITH_CONTEXT_PROMPT.format(
        company_name=company_name,
        leadership_text=leadership_text,
        jd_text=jd_text,
        principles_json=principles_json,
        company_key=company_key,
    )

    schema = {
        "company": "",
        "required_skills": [],
        "preferred_skills": [],
        "soft_skills": [],
        "seniority_level": "",
        "education_requirements": "",
        "experience_years": "",
        "industry_keywords": [],
        "role_summary": "",
        "hiring_motivation": "",
        "leadership_alignment": {},
        "red_flags": [],
        "suggestions": [],
    }

    result = await llm_client.structured_output(prompt, schema)

    if "error" in result:
        return _fallback_parse(jd_text, company, profile)

    return result


async def _parse_generic(jd_text: str, company: str) -> Dict[str, Any]:
    """Fallback to the existing generic JD parser, enriched with local alignment."""
    from services.ai.pipeline import parse_jd

    generic = await parse_jd(jd_text)
    generic["company"] = company.strip().lower()
    generic["leadership_alignment"] = _score_leadership_alignment(jd_text)
    generic["red_flags"] = []
    generic["suggestions"] = [
        "公司暂无专属画像，使用通用优化策略",
        "建议量化所有成就",
        "使用 JD 中的关键词",
    ]
    return generic


def _fallback_parse(
    jd_text: str,
    company: str,
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """Pure-local fallback when LLM is unavailable."""
    lines = [line.strip() for line in jd_text.split("\n") if line.strip()]

    skills = _extract_skills_local(jd_text)
    alignment = _score_leadership_alignment(jd_text)

    suggestions = list(profile.get("tips", []))
    if not _has_quantification(jd_text):
        suggestions.append("建议添加量化指标")

    return {
        "company": company.strip().lower(),
        "required_skills": skills.get("required", []),
        "preferred_skills": skills.get("preferred", []),
        "soft_skills": skills.get("soft", []),
        "seniority_level": _detect_seniority(jd_text),
        "education_requirements": "",
        "experience_years": "",
        "industry_keywords": [],
        "role_summary": lines[0][:100] if lines else "",
        "hiring_motivation": "",
        "leadership_alignment": alignment,
        "red_flags": ["LLM 不可用，分析结果有限"],
        "suggestions": suggestions,
    }


def _extract_skills_local(text: str) -> Dict[str, List[str]]:
    tech_keywords = [
        "python",
        "java",
        "go",
        "rust",
        "c++",
        "typescript",
        "javascript",
        "react",
        "vue",
        "angular",
        "node.js",
        "spring",
        "django",
        "flask",
        "docker",
        "kubernetes",
        "aws",
        "gcp",
        "azure",
        "redis",
        "kafka",
        "mysql",
        "postgresql",
        "mongodb",
        "elasticsearch",
        "graphql",
        "rest",
        "grpc",
        "microservice",
        "linux",
        "git",
        "ci/cd",
    ]
    text_lower = text.lower()
    found = [kw for kw in tech_keywords if kw in text_lower]

    required: List[str] = []
    preferred: List[str] = []

    for line in text.split("\n"):
        line_lower = line.lower()
        for kw in found:
            if kw not in required and kw not in preferred:
                if any(
                    m in line_lower for m in ["要求", "必须", "require", "must", "必备"]
                ):
                    required.append(kw)
                elif any(
                    m in line_lower
                    for m in ["优先", "加分", "nice", "preferred", "plus"]
                ):
                    preferred.append(kw)

    remaining = [kw for kw in found if kw not in required and kw not in preferred]
    required.extend(remaining)

    return {"required": required, "preferred": preferred, "soft": []}


def _detect_seniority(text: str) -> str:
    text_lower = text.lower()
    if any(kw in text_lower for kw in ["初级", "junior", "assistant", "1-2"]):
        return "junior"
    if any(
        kw in text_lower
        for kw in ["高级", "资深", "senior", "staff", "principal", "专家"]
    ):
        return "senior"
    return "mid"


def _has_quantification(text: str) -> bool:
    return bool(re.search(r"\d+%|\d+x|\d+\+|\$|¥|万|亿", text))
