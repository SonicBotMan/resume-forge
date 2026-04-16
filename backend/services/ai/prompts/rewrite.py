"""Rewrite prompt for resume language conversion."""

REWRITE_PROMPT = """你是一个资深的简历优化专家。请将以下工作描述改写为更专业的简历语言。

改写原则：
1. 动词开头：用"主导""负责""设计""推动""优化"等
2. 量化成果：把模糊描述转为数据（如"NPS从35提升至52"）
3. 突出影响：强调对业务的影响和决策的作用
4. 精简有力：每条描述控制在2行以内
5. 不夸大不编造：基于原文改写，不添加原文没有的信息

原始描述：
---
{raw_description}
---

改写后的简历描述：
"""


def get_rewrite_prompt(raw_description: str) -> str:
    return REWRITE_PROMPT.format(raw_description=raw_description)
