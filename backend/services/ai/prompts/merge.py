"""Merge prompt for combining duplicate projects."""

MERGE_PROMPT = """以下是AI从不同材料中提取的两个关于同一项目的信息：
来源1（来自"{source1}"）：
{project1}
来源2（来自"{source2}"）：
{project2}

请合并为一份完整的项目经历，要求：
1. 保留两个来源中所有独特信息
2. 解决冲突（如时间不一致，取更具体的）
3. 使用更专业的"简历语言"重新表述
4. 确保STAR结构完整
5. Result部分优先使用量化数据

输出合并后的JSON（格式同上）。
"""


def get_merge_prompt(source1: str, project1: str, source2: str, project2: str) -> str:
    return MERGE_PROMPT.format(
        source1=source1,
        project1=project1,
        source2=source2,
        project2=project2,
    )
