"""AI one-click resume optimization with multiple style versions."""

OPTIMIZE_PROMPT = """你是一位顶尖的简历优化专家，精通 ATS 系统和 HR 筛选规则。

## 目标职位解析
{jd_parsed}

## 原始简历项目经历
---
{project_text}
---

## 任务
请为上述项目经历生成 **{num_versions}** 个不同风格的优化版本。

### 风格要求：
1. **v1 - 数据驱动型**: 用数据和指标说话，强调可量化的业务成果。适合技术岗位、运营岗位。
2. **v2 - 影响力导向型**: 强调领导力、决策影响和战略价值。适合管理岗位、高级岗位。
3. **v3 - 技能匹配型**: 精准对接 JD 要求的技能关键词，提升 ATS 通过率。适合投递大公司、外企。

### 优化原则：
- 遵循 STAR 法则（Situation-Task-Action-Result）
- 每条描述以强动词开头（主导、设计、推动、优化、重构）
- 包含 JD 中的关键技能词汇
- 不夸大、不编造，基于原始内容优化
- 控制每条描述在 1-2 行以内
- 量化成果使用具体数字

### ATS 分数预估：
对每个版本预估相比原文的 ATS 分数变化（+N 格式），基于以下因素：
- JD 关键词覆盖率
- 量化指标丰富度
- 软技能体现程度

## 输出格式

严格返回以下JSON（不要包含任何其他内容）：
{{
    "versions": [
        {{
            "version_id": "v1",
            "style": "数据驱动",
            "content": "优化后的项目描述文本...",
            "ats_score_delta": "+15",
            "key_changes": ["添加了量化指标", "嵌入了Python关键词"]
        }},
        {{
            "version_id": "v2",
            "style": "影响力导向",
            "content": "优化后的项目描述文本...",
            "ats_score_delta": "+12",
            "key_changes": ["突出领导力", "强调战略影响"]
        }},
        {{
            "version_id": "v3",
            "style": "技能匹配",
            "content": "优化后的项目描述文本...",
            "ats_score_delta": "+18",
            "key_changes": ["密集嵌入JD关键词", "优化技能表述"]
        }}
    ]
}}
"""


def get_optimize_prompt(
    jd_parsed: str,
    project_text: str,
    num_versions: int = 3,
) -> str:
    """Generate optimization prompt.

    Args:
        jd_parsed: JSON string of parsed JD.
        project_text: Original project experience text.
        num_versions: Number of optimization versions to generate.

    Returns:
        Formatted prompt string.
    """
    return OPTIMIZE_PROMPT.format(
        jd_parsed=jd_parsed,
        project_text=project_text,
        num_versions=num_versions,
    )
