"""Quantified achievement patterns recognized by top-tier companies."""

from typing import Dict, List

ACHIEVEMENT_PATTERNS: Dict[str, List[str]] = {
    "scale": [
        "服务 {count}+ 用户，日均请求 {qps}",
        "将系统容量从 {old} 扩展到 {new}（增长 {multiple} 倍）",
        "支持双11峰值 {qps} QPS，0 故障",
        "系统支撑 {concurrent} 并发连接，P99 延迟 {latency}ms",
        "日均处理 {volume} 条数据，峰值吞吐量 {throughput}",
    ],
    "performance": [
        "将响应时间从 {old} 优化至 {new}（提升 {percentage}%）",
        "性能提升 {times} 倍，延迟降低至 {latency}ms",
        "通过 {method} 优化，CPU 使用率从 {old}% 降至 {new}%",
        "内存占用降低 {percentage}%，GC 停顿减少 {times} 倍",
        "首屏加载时间从 {old}s 降至 {new}s",
    ],
    "revenue": [
        "为公司创造 {revenue} 收入",
        "通过 {feature} 功能带来 {increase}% 收入增长",
        "优化转化率 {old}% → {new}%，提升收入 {amount}",
        "推动 {metric} 提升 {percentage}%，贡献 GMV {amount}",
        "新功能上线后季度收入增长 {percentage}%",
    ],
    "cost": [
        "节省 {cost} 基础成本",
        "通过自动化减少 {count} 人/天工作量",
        "资源优化降低 {percentage}% 云服务费用",
        "服务器数量减少 {percentage}%，月节省 {amount}",
        "通过 {method} 将运维成本降低 {percentage}%",
    ],
    "team": [
        "带领 {size} 人团队完成项目",
        "辅导 {count} 名初级工程师，{percentage}% 在一年内晋升",
        "招聘并组建 {size} 人技术团队",
        "推动 {count} 场技术分享，提升团队工程效能",
        "建立 {process} 机制，团队交付效率提升 {percentage}%",
    ],
    "reliability": [
        "系统可用性达到 {availability}%，全年故障时间 < {downtime}",
        "将线上故障率降低 {percentage}%，MTTR 从 {old} 缩短至 {new}",
        "设计容灾方案，实现跨 {regions} 区域双活",
        "通过混沌工程发现并修复 {count} 个潜在故障点",
        "零故障运行 {days} 天，支撑 {scale} 级别业务",
    ],
    "innovation": [
        "设计并落地 {system} 系统，获公司级技术创新奖",
        "申请 {count} 项技术专利",
        "开源项目获 {stars} GitHub stars",
        "在 {conference} 发表技术论文，被引用 {count} 次",
        "技术方案被 {count} 个团队采纳，成为公司标准",
    ],
}

# Metrics that resonate strongly with specific company types
COMPANY_METRIC_MAP: Dict[str, List[str]] = {
    "apple": [
        "user satisfaction score",
        "app store rating improvement",
        "accessibility compliance",
        "privacy compliance rate",
    ],
    "google": [
        "QPS / queries per second",
        "p99 latency",
        "billions of users impacted",
        "open source contributions",
    ],
    "amazon": [
        "$ cost savings",
        "% revenue increase",
        "customer satisfaction (CSAT)",
        "time to market reduction",
    ],
    "bytedance": [
        "CTR improvement",
        "DAU/MAU growth",
        "retention rate",
        "A/B test statistical significance",
    ],
    "tencent": [
        "DAU / MAU",
        "payment volume (CNY)",
        "social engagement rate",
        "concurrent online users",
    ],
    "alibaba": [
        "GMV contribution",
        "Double 11 peak QPS",
        "merchant growth rate",
        "order fulfillment rate",
    ],
}


def get_patterns_for_company(company: str) -> Dict[str, List[str]]:
    """Return achievement patterns plus company-specific metrics."""
    from services.ai.company_engine.company_profiles import get_profile

    all_patterns = dict(ACHIEVEMENT_PATTERNS)
    profile = get_profile(company)
    if profile:
        key = company.strip().lower()
        if key in COMPANY_METRIC_MAP:
            all_patterns["company_specific"] = COMPANY_METRIC_MAP[key]
    return all_patterns
