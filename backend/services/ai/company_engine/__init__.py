"""Company-specific resume optimization engine.

Usage:
    from services.ai.company_engine import (
        get_profile,
        parse_jd_with_company_context,
        optimize_for_company,
        predict_interview_questions,
    )
"""

from services.ai.company_engine.company_profiles import (
    COMPANY_PROFILES,
    get_profile,
    get_company_name,
    list_companies,
)
from services.ai.company_engine.achievement_library import (
    ACHIEVEMENT_PATTERNS,
    COMPANY_METRIC_MAP,
    get_patterns_for_company,
)
from services.ai.company_engine.company_jd_parser import (
    parse_jd_with_company_context,
)
from services.ai.company_engine.company_resume_optimizer import (
    OptimizeResult,
    OptimizeVersion,
    optimize_for_company,
)
from services.ai.company_engine.interview_predictor import (
    predict_interview_questions,
)

__all__ = [
    "COMPANY_PROFILES",
    "ACHIEVEMENT_PATTERNS",
    "COMPANY_METRIC_MAP",
    "get_profile",
    "get_company_name",
    "list_companies",
    "get_patterns_for_company",
    "parse_jd_with_company_context",
    "OptimizeResult",
    "OptimizeVersion",
    "optimize_for_company",
    "predict_interview_questions",
]
