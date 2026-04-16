"""Company-specific resume optimization with multi-version output."""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

from services.ai.client import llm_client
from services.ai.company_engine.company_profiles import get_profile


@dataclass
class OptimizeVersion:
    version_id: str = ""
    name: str = ""
    content: str = ""
    company_fit_score: int = 0
    highlighted_changes: List[str] = field(default_factory=list)


@dataclass
class OptimizeResult:
    company: str = ""
    company_name: str = ""
    versions: List[OptimizeVersion] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)


_COMPANY_OPTIMIZE_PROMPT = """你是一位针对 {company_name} 的简历优化专家。
你必须确保简历能够通过 {company_name} 的 ATS 筛选和文化面试。

## 目标公司画像
{company_profile_text}

## 公司偏好的动词
{preferred_verbs}

## 公司偏好的影响力量化模式
{impact_patterns}

## 职位分析
{jd_analysis_json}

## 原始简历内容
---
{resume_text}
---

## 优化任务
请生成 **2** 个针对 {company_name} 优化的简历版本：

### 版本 1：技术深度版
- 使用公司偏好的动词开头
- 嵌入公司文化关键词
- 强调与公司领导力准则对齐的成就
- 量化所有成果

### 版本 2：影响力量化版
- 突出与公司领导力准则最匹配的项目经历
- 用公司认可的量化方式描述成就
- 从公司关注的角度重新组织经历描述
- 强调跨团队协作和影响力

### 优化原则：
- 不夸大、不编造，基于原始内容优化
- 每条描述以强动词开头
- 包含具体数字和百分比
- 融入 JD 关键词
- 体现公司的核心价值观

## 输出格式

严格返回以下 JSON（不要包含任何其他内容）：
{{
    "versions": [
        {{
            "version_id": "v1",
            "name": "技术深度版",
            "content": "优化后的完整简历内容...",
            "company_fit_score": 85,
            "highlighted_changes": [
                "将'负责推荐系统' → '设计并部署日活1亿+用户的推荐系统'",
                "添加: 'QPS提升40%，延迟降低至50ms'"
            ]
        }},
        {{
            "version_id": "v2",
            "name": "影响力量化版",
            "content": "优化后的完整简历内容...",
            "company_fit_score": 82,
            "highlighted_changes": []
        }}
    ]
}}
"""

_GENERIC_OPTIMIZE_PROMPT = """你是一位简历优化专家，精通 ATS 系统筛选规则。

## 职位分析
{jd_analysis_json}

## 原始简历内容
---
{resume_text}
---

## 优化任务
请生成 **2** 个优化版本：

### 版本 1：技能匹配版
- 精准嵌入 JD 关键词
- 使用强动词开头
- 量化成果

### 版本 2：影响力版
- 突出业务影响
- 强调领导力和协作
- 量化贡献

## 输出格式

严格返回以下 JSON（不要包含任何其他内容）：
{{
    "versions": [
        {{
            "version_id": "v1",
            "name": "技能匹配版",
            "content": "优化后的完整简历内容...",
            "company_fit_score": 75,
            "highlighted_changes": []
        }},
        {{
            "version_id": "v2",
            "name": "影响力版",
            "content": "优化后的完整简历内容...",
            "company_fit_score": 72,
            "highlighted_changes": []
        }}
    ]
}}
"""


def _profile_to_text(profile: Dict[str, Any]) -> str:
    parts = [
        f"核心价值观关键词: {', '.join(profile.get('culture_keywords', []))}",
        "领导力准则:",
    ]
    for p in profile.get("leadership_principles", []):
        parts.append(f"  - {p}")
    return "\n".join(parts)


def _local_fit_score(resume_text: str, profile: Dict[str, Any]) -> int:
    """Rough local estimate of how well resume matches company culture."""
    resume_lower = resume_text.lower()
    culture_hits = sum(
        1 for kw in profile.get("culture_keywords", []) if kw.lower() in resume_lower
    )
    verb_hits = sum(
        1 for v in profile.get("preferred_verbs", []) if v.lower() in resume_lower
    )
    total_keywords = len(profile.get("culture_keywords", [])) + len(
        profile.get("preferred_verbs", [])
    )
    if total_keywords == 0:
        return 50
    raw = (culture_hits + verb_hits) / total_keywords
    return min(int(raw * 100), 95)


async def optimize_for_company(
    resume_text: str,
    company: str,
    jd_analysis: Dict[str, Any],
) -> OptimizeResult:
    """Optimize resume for a specific target company.

    When the company has a dedicated profile, produces company-tailored
    versions. Falls back to generic optimization otherwise.
    """
    profile = get_profile(company)
    company_name = profile["name"] if profile else company
    company_key = company.strip().lower()
    tips = (
        list(profile.get("tips", []))
        if profile
        else [
            "量化所有成就",
            "使用 JD 中的关键词",
            "以强动词开头每条描述",
        ]
    )

    jd_json = json.dumps(jd_analysis, ensure_ascii=False)

    if profile:
        prompt = _COMPANY_OPTIMIZE_PROMPT.format(
            company_name=company_name,
            company_profile_text=_profile_to_text(profile),
            preferred_verbs=", ".join(profile.get("preferred_verbs", [])),
            impact_patterns="\n".join(
                f"- {p}" for p in profile.get("impact_patterns", [])
            ),
            jd_analysis_json=jd_json,
            resume_text=resume_text,
        )
    else:
        prompt = _GENERIC_OPTIMIZE_PROMPT.format(
            jd_analysis_json=jd_json,
            resume_text=resume_text,
        )

    schema = {
        "versions": [
            {
                "version_id": "",
                "name": "",
                "content": "",
                "company_fit_score": 0,
                "highlighted_changes": [],
            }
        ]
    }

    result = await llm_client.structured_output(prompt, schema)

    if "error" in result or "versions" not in result:
        return OptimizeResult(
            company=company_key,
            company_name=company_name,
            versions=[
                OptimizeVersion(
                    version_id="v1",
                    name="原文（优化失败）",
                    content=resume_text,
                    company_fit_score=_local_fit_score(resume_text, profile)
                    if profile
                    else 50,
                    highlighted_changes=["LLM 不可用，返回原始内容"],
                )
            ],
            tips=tips,
        )

    versions: List[OptimizeVersion] = []
    for v in result["versions"]:
        versions.append(
            OptimizeVersion(
                version_id=v.get("version_id", "v1"),
                name=v.get("name", ""),
                content=v.get("content", ""),
                company_fit_score=v.get("company_fit_score", 0),
                highlighted_changes=v.get("highlighted_changes", []),
            )
        )

    return OptimizeResult(
        company=company_key,
        company_name=company_name,
        versions=versions,
        tips=tips,
    )
