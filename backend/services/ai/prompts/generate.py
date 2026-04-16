"""Generate prompt for resume generation."""

from typing import Optional

GENERATE_PROMPT = """
基于以下职业经历数据，生成一份专业的简历内容。

项目经历：
{projects}

技能列表：
{skills}

工作成果：
{achievements}

请生成以下格式的JSON（只返回JSON，不要其他内容）：
{{
    "summary": "2-3句话的专业简介，突出核心能力和主要成就",
    "experience": ["工作经历1", "工作经历2"],
    "projects": [
        {{
            "name": "项目名称",
            "role": "担任角色",
            "start_date": "开始时间",
            "end_date": "结束时间",
            "description": "项目简介（1-2句话概述项目内容和你的职责）",
            "situation": "项目背景和起因（1-2句话）",
            "task": "你的具体职责和目标（1-2句话）",
            "action": "你采取的关键行动和方法（2-3句话）",
            "result": "可量化的成果和影响（必须包含数字或百分比）"
        }}
    ],
    "skills": ["技能1", "技能2"],
    "education": ["教育经历1"]
}}

关键要求：
1. projects数组中的每个项目必须包含完整的STAR字段（situation、task、action、result），不能只有标题
2. result字段必须包含量化数据（如"提升了30%"、"增加了5000用户"等）
3. 从提供的项目经历数据中重新组织和优化语言，使其更加专业和精炼
4. 保留原始数据中的所有关键信息，不要遗漏重要细节
"""

JD_SECTION = "目标岗位描述：{jd_text}\n\n请针对该岗位优化简历内容，突出相关经验。"


def get_generate_prompt(projects: str, skills: str, achievements: str, jd_text: Optional[str] = None) -> str:
    prompt = GENERATE_PROMPT.format(
        projects=projects,
        skills=skills,
        achievements=achievements,
    )
    if jd_text:
        prompt = JD_SECTION.format(jd_text=jd_text) + prompt
    return prompt
