"""Classification prompt for work reports and career materials."""

CLASSIFY_PROMPT = """你是一个简历分析师。判断以下材料片段是否包含有价值的职业经历信息。

包含有价值信息的类型：
- A: 公司/职位信息
- B: 工作内容/项目（哪怕是周报中的完成项）
- C: 量化成果/指标（任何数字、百分比、排名等）
- D: 技能/工具/方法论
- E: OKR/目标相关
- F: 团队协作/跨部门配合
- G: 教育背景

无关信息：
- N: 纯粹格式内容、广告、感谢语等

注意：周报、月报、OKR汇报中的工作内容都是有效的职业经历素材，哪怕是"日常完成的小任务"也要识别为B类。

 片段内容：
---
<user_content>
{chunk_text}
</user_content>
---

请以JSON格式输出：
{{"categories": ["B", "C"], "relevance": 0.0-1.0, "brief_summary": "一句话概括这个片段的核心内容"}}

只要有工作相关内容，relevance不要低于0.5。
"""


def get_classify_prompt(chunk_text: str) -> str:
    return CLASSIFY_PROMPT.format(chunk_text=chunk_text)
