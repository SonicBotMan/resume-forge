"""ATS scoring prompt and calculation logic."""

import re
from typing import Dict, List, Any

ATS_SCORE_PROMPT = """你是一位 ATS（Applicant Tracking System）简历评分专家。

## 目标职位解析结果
{jd_parsed}

## 候选人简历内容
---
{resume_text}
---

## 评分任务

请基于以下五个维度对简历进行 ATS 评分：

1. **必选技能匹配率（权重40%）**: 检查简历中是否包含 JD 要求的所有必选技能
2. **加分技能匹配率（权重20%）**: 检查简历中包含哪些加分技能
3. **软技能匹配率（权重10%）**: 检查简历中是否体现了要求的软技能
4. **关键词密度（权重15%）**: 检查 JD 行业关键词在简历中的出现频率和自然度
5. **量化成果（权重15%）**: 检查简历中是否有具体的数字、百分比、业绩指标

## 量化成果识别
请找出简历中所有包含量化数据的描述，例如：
- "提升了X%"
- "减少了X小时"
- "管理X人团队"
- "年营收X万"
- "用户量达到X"

## 输出格式

严格返回以下JSON（不要包含任何其他内容）：
{{
    "total_score": 75,
    "breakdown": {{
        "required_skills": {{
            "score": 80,
            "matched": ["Python", "SQL"],
            "missing": ["Redis"]
        }},
        "preferred_skills": {{
            "score": 60,
            "matched": ["AWS"],
            "missing": ["Docker"]
        }},
        "soft_skills": {{
            "score": 100,
            "matched": ["团队协作", "沟通能力"]
        }},
        "keyword_density": {{
            "score": 70,
            "density": 0.05
        }},
        "quantification": {{
            "score": 75,
            "examples": ["提升性能200%", "管理10人团队"]
        }}
    }},
    "improvement_suggestions": [
        "添加 Redis 经验描述",
        "量化支付系统用户量",
        "补充 Docker 容器化经验"
    ]
}}
"""


def get_ats_score_prompt(jd_parsed: Dict[str, Any], resume_text: str) -> str:
    """Generate ATS scoring prompt.

    Args:
        jd_parsed: Parsed JD structure from jd_parse.
        resume_text: Raw resume text content.

    Returns:
        Formatted prompt string.
    """
    import json

    return ATS_SCORE_PROMPT.format(
        jd_parsed=json.dumps(jd_parsed, ensure_ascii=False, indent=2),
        resume_text=resume_text,
    )


def calculate_local_ats_score(
    resume_text: str,
    required_skills: List[str],
    preferred_skills: List[str],
    soft_skills: List[str],
    industry_keywords: List[str],
) -> Dict[str, Any]:
    """Calculate a preliminary ATS score using local keyword matching.

    This provides a fast, deterministic baseline before the LLM deep analysis.

    Args:
        resume_text: Resume text in lowercase.
        required_skills: Must-have skills from JD.
        preferred_skills: Nice-to-have skills from JD.
        soft_skills: Soft skill requirements from JD.
        industry_keywords: Industry-specific keywords from JD.

    Returns:
        Dict with breakdown scores and total.
    """
    text_lower = resume_text.lower()

    def _match_rate(skills: List[str]) -> tuple:
        matched = []
        missing = []
        for skill in skills:
            skill_lower = skill.lower()
            variants = [skill_lower]
            if len(skill_lower) >= 2:
                variants.append(skill_lower)

            found = any(v in text_lower for v in variants)
            if found:
                matched.append(skill)
            else:
                missing.append(skill)
        return matched, missing

    # Required skills (40% weight)
    req_matched, req_missing = _match_rate(required_skills)
    req_score = int((len(req_matched) / max(len(required_skills), 1)) * 100)

    # Preferred skills (20% weight)
    pref_matched, pref_missing = _match_rate(preferred_skills)
    pref_score = int((len(pref_matched) / max(len(preferred_skills), 1)) * 100)

    # Soft skills (10% weight)
    soft_matched, _ = _match_rate(soft_skills)
    soft_score = int((len(soft_matched) / max(len(soft_skills), 1)) * 100)

    # Keyword density (15% weight)
    kw_count = sum(1 for kw in industry_keywords if kw.lower() in text_lower)
    density = kw_count / max(len(text_lower.split()), 1)
    kw_score = min(int(density * 2000), 100)  # Scale: 5% density = 100

    # Quantification (15% weight)
    quant_patterns = [
        r"\d+%",
        r"\d+万",
        r"\d+亿",
        r"\d+人",
        r"\d+个",
        r"\d+倍",
        r"\d+次",
        r"\d+小时",
        r"\d+天",
        r"提升\s*\d+",
        r"减少\s*\d+",
        r"增长\s*\d+",
        r"节省\s*\d+",
        r"完成\s*\d+",
    ]
    quant_examples = []
    for pattern in quant_patterns:
        matches = re.findall(rf".{{0,15}}{pattern}.{{0,15}}", resume_text)
        quant_examples.extend(matches[:3])

    quant_score = min(len(quant_examples) * 20, 100)

    total_score = (
        req_score * 40
        + pref_score * 20
        + soft_score * 10
        + kw_score * 15
        + quant_score * 15
    ) // 100

    # Generate improvement suggestions
    suggestions = []
    for skill in req_missing[:3]:
        suggestions.append(f"添加 {skill} 相关经验描述")
    for skill in pref_missing[:2]:
        suggestions.append(f"补充 {skill} 加分技能")
    if quant_score < 60:
        suggestions.append("增加量化成果描述（使用具体数字和百分比）")

    return {
        "total_score": min(total_score, 100),
        "breakdown": {
            "required_skills": {
                "score": req_score,
                "matched": req_matched,
                "missing": req_missing,
            },
            "preferred_skills": {
                "score": pref_score,
                "matched": pref_matched,
                "missing": pref_missing,
            },
            "soft_skills": {
                "score": soft_score,
                "matched": soft_matched,
            },
            "keyword_density": {
                "score": kw_score,
                "density": round(density, 4),
            },
            "quantification": {
                "score": quant_score,
                "examples": quant_examples[:5],
            },
        },
        "improvement_suggestions": suggestions[:5],
    }
