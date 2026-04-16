"""Match prompt for job matching."""

MATCH_PROMPT = """以下是目标岗位的JD关键词和候选项目经历：
岗位关键词：{jd_keywords}
候选项目：
{project}

请评估这个项目经历与目标岗位的相关性，输出：
{{"relevance_score": 0.85, "matching_points": ["数据驱动决策", "商业化经验"], "gaps": ["缺少B端经验"], "suggested_adjustments": "突出商业化成果，弱化C端内容"}}
"""


def get_match_prompt(jd_keywords: str, project: str) -> str:
    return MATCH_PROMPT.format(jd_keywords=jd_keywords, project=project)
