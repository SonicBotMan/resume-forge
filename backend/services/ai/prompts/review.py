from typing import Optional


ROLE_PROMPTS = {
    "hr": """你是一位经验丰富的外企招聘HR。请从以下角度审视这份简历：

1. 简历格式和可读性
2. 关键词密度和ATS友好度
3. 信息完整性和逻辑性
4. 是否能通过HR的30秒初筛
5. 亮点是否突出

简历内容：
<user_content>
{resume_content}
</user_content>
</user_content>

{jd_section}

请返回JSON格式：
{{
    "role": "招聘HR",
    "problems": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"],
    "score_impact": "positive/neutral/negative",
    "key_insight": "一句话总结"
}}""",

    "headhunter": """你是一位资深猎头顾问。请从以下角度审视这份简历：

1. 市场竞争力定位
2. 薪资谈判的优劣势
3. 候选人的独特价值主张
4. 与目标岗位的市场匹配度
5. 职业发展轨迹的合理性

简历内容：
<user_content>
{resume_content}
</user_content>

{jd_section}

请返回JSON格式：
{{
    "role": "猎头顾问",
    "problems": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"],
    "score_impact": "positive/neutral/negative",
    "key_insight": "一句话总结"
}}""",

    "interviewer": """你是一位技术面试官。请从以下角度审视这份简历：

1. 技术深度的体现
2. 项目经历的真实性和含金量
3. 成果量化的说服力
4. 技术栈匹配度
5. 可能会追问的问题点

简历内容：
<user_content>
{resume_content}
</user_content>

{jd_section}

请返回JSON格式：
{{
    "role": "面试官",
    "problems": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"],
    "score_impact": "positive/neutral/negative",
    "key_insight": "一句话总结"
}}""",

    "manager": """你是一位部门经理。请从以下角度审视这份简历：

1. 团队协作和领导力潜质
2. 业务理解和问题解决能力
3. 项目管理和交付能力
4. 与团队文化的适配度
5. 培养潜力

简历内容：
<user_content>
{resume_content}
</user_content>

{jd_section}

请返回JSON格式：
{{
    "role": "部门经理",
    "problems": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"],
    "score_impact": "positive/neutral/negative",
    "key_insight": "一句话总结"
}}""",

    "expert": """你是一位行业专家。请从以下角度审视这份简历：

1. 行业趋势和方向的把握
2. 专业术语的准确使用
3. 职业发展路径的前瞻性
4. 行业人脉和资源的体现
5. 未来3-5年的成长空间

简历内容：
<user_content>
{resume_content}
</user_content>

{jd_section}

请返回JSON格式：
{{
    "role": "行业专家",
    "problems": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"],
    "score_impact": "positive/neutral/negative",
    "key_insight": "一句话总结"
}}""",
}

SYNTHESIS_PROMPT = """你是一位简历优化总顾问。以下是从5个不同角色视角对简历的评审意见。

HR评审：
{hr_review}

猎头评审：
{headhunter_review}

面试官评审：
{interviewer_review}

部门经理评审：
{manager_review}

行业专家评审：
{expert_review}

请综合以上所有角色的意见，返回JSON格式：
{{
    "overall_assessment": "综合评价（2-3句话）",
    "critical_fixes": ["必须修改的问题1", "必须修改的问题2"],
    "recommended_improvements": ["建议改进1", "建议改进2"],
    "resume_revisions": {{
        "summary": "建议的简历简介修改",
        "key_additions": ["需要增加的内容1", "需要增加的内容2"],
        "key_removals": ["需要删除或弱化的内容1"],
        "tone_adjustment": "整体语气调整建议"
    }},
    "interview_plan": {{
        "likely_questions": ["面试官可能问的问题1", "问题2", "问题3"],
        "prepared_answers": ["对应的回答策略1", "策略2", "策略3"],
        "weakness_mitigation": "如何化解简历中的薄弱环节",
        "highlight_strategy": "面试中如何突出优势"
    }}
}}"""


def get_role_prompt(role: str, resume_content: str, jd_text: Optional[str] = None) -> str:
    template = ROLE_PROMPTS.get(role)
    if not template:
        raise ValueError(f"Unknown role: {role}")
    jd_section = f"目标岗位信息：\n{jd_text}" if jd_text else ""
    return template.format(resume_content=resume_content, jd_section=jd_section)


def get_synthesis_prompt(reviews: dict, resume_content: str) -> str:
    return SYNTHESIS_PROMPT.format(
        hr_review=reviews.get("hr", "无"),
        headhunter_review=reviews.get("headhunter", "无"),
        interviewer_review=reviews.get("interviewer", "无"),
        manager_review=reviews.get("manager", "无"),
        expert_review=reviews.get("expert", "无"),
    )
