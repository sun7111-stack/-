import re
from typing import Optional, List

from sqlalchemy.orm import Session
from models.carbon import EmissionFactorItem

def _extract_year(version: str) -> Optional[int]:
    if not version:
        return None
    match = re.search(r"(19|20)\d{2}", version)
    if not match:
        return None
    return int(match.group(0))


def _pick_by_year(candidates: List[EmissionFactorItem], year: Optional[int]) -> Optional[EmissionFactorItem]:
    if not candidates:
        return None

    def score(item: EmissionFactorItem) -> int:
        if item.year:
            return int(item.year)
        parsed = _extract_year(item.version or "")
        return parsed or 0

    if year is None:
        return sorted(candidates, key=score, reverse=True)[0]

    not_greater = [x for x in candidates if score(x) <= year and score(x) > 0]
    if not_greater:
        return sorted(not_greater, key=score, reverse=True)[0]
    return sorted(candidates, key=score, reverse=True)[0]


def get_factor(
    db: Session,
    activity_type: str,
    industry_type: str = "general",
    region: str = "全国",
    year: Optional[int] = None,
    method: str = "default",
    version: str = None,
) -> dict:
    """
    统一因子查询函数（工程化隔离层）
    查询优先级:
    1. activity_type + industry_type + region
    2. activity_type + industry_type + 全国
    3. activity_type + general + 全国
    """
    # 基础查询过滤（activity + method）
    query = db.query(EmissionFactorItem).filter(EmissionFactorItem.activity_type == activity_type)
    query = query.filter((EmissionFactorItem.method == method) | (EmissionFactorItem.method == "default"))

    if version:
        query = query.filter(EmissionFactorItem.version == version)

    # 1. 第一优先：精准匹配 (activity_type + industry_type + region)
    candidates = query.filter(
        EmissionFactorItem.industry_type == industry_type,
        EmissionFactorItem.region == region
    ).all()
    factor = _pick_by_year(candidates, year)
    if factor:
        return _format_factor(factor, method=method, fallback_level="exact")

    # 2. 第二优先：降级到全国 (activity_type + industry_type + 全国)
    if region != "全国":
        candidates = query.filter(
            EmissionFactorItem.industry_type == industry_type,
            EmissionFactorItem.region == "全国"
        ).all()
        factor = _pick_by_year(candidates, year)
        if factor:
            return _format_factor(factor, method=method, fallback_level="region_fallback")

    # 3. 第三优先：降级到通用行业和全国 (activity_type + general + 全国)
    if industry_type != "general" or region != "全国":
        candidates = query.filter(
            EmissionFactorItem.industry_type == "general",
            EmissionFactorItem.region == "全国"
        ).all()
        factor = _pick_by_year(candidates, year)
        if factor:
            return _format_factor(factor, method=method, fallback_level="industry_region_fallback")

    # 若全未命中，返回默认空结果
    return {
        "factor_id": None,
        "value": 0.0,
        "unit": "unknown",
        "source": "未找到匹配因子",
        "year": year,
        "region": region,
        "method": method,
        "version_tag": "",
        "source_type": "unknown",
        "dq_factor_level": "D",
        "gsd_factor": 0.2,
        "match_reason": "no_match_default_zero",
        "fallback_level": "none",
    }

def _format_factor(factor: EmissionFactorItem, method: str, fallback_level: str) -> dict:
    y = factor.year or _extract_year(factor.version or "")
    return {
        "factor_id": factor.id,
        "value": factor.factor_value,
        "unit": factor.factor_unit,
        "source": f"{factor.source} ({factor.version})",
        "year": y,
        "region": factor.region,
        "method": factor.method or method,
        "version_tag": factor.version_tag or factor.version,
        "source_type": factor.source_type or "government_factor",
        "dq_factor_level": factor.dq_factor_level or "C",
        "gsd_factor": factor.gsd_factor if factor.gsd_factor is not None else 0.1,
        "match_reason": f"activity={factor.activity_type}; industry={factor.industry_type}; region={factor.region}; fallback={fallback_level}",
        "fallback_level": fallback_level,
    }

class FactorStore:
    """策略层使用的查询器实例，封装 db_session 和当前上下文环境变量"""
    def __init__(self, db: Session, region: str = "全国", year: Optional[int] = None, method: str = "default", version: str = None):
        self.db = db
        self.region = region
        self.year = year
        self.method = method
        self.version = version
        
    def get_factor(self, activity_type: str, industry_type: str = "general") -> dict:
        """对接底层暴露的 get_factor 统一函数"""
        return get_factor(
            db=self.db, 
            activity_type=activity_type, 
            industry_type=industry_type, 
            region=self.region, 
            year=self.year,
            method=self.method,
            version=self.version
        )
