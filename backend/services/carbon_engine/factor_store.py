from sqlalchemy.orm import Session
from models.carbon import EmissionFactorItem

def get_factor(db: Session, activity_type: str, industry_type: str = "general", region: str = "全国", version: str = None) -> dict:
    """
    统一因子查询函数（工程化隔离层）
    查询优先级:
    1. activity_type + industry_type + region
    2. activity_type + industry_type + 全国
    3. activity_type + general + 全国
    """
    # 基础查询过滤
    query = db.query(EmissionFactorItem).filter(EmissionFactorItem.activity_type == activity_type)
    if version:
        query = query.filter(EmissionFactorItem.version == version)

    # 1. 第一优先：精准匹配 (activity_type + industry_type + region)
    factor = query.filter(
        EmissionFactorItem.industry_type == industry_type,
        EmissionFactorItem.region == region
    ).first()
    
    if factor:
        return _format_factor(factor)

    # 2. 第二优先：降级到全国 (activity_type + industry_type + 全国)
    if region != "全国":
        factor = query.filter(
            EmissionFactorItem.industry_type == industry_type,
            EmissionFactorItem.region == "全国"
        ).first()
        
        if factor:
            return _format_factor(factor)

    # 3. 第三优先：降级到通用行业和全国 (activity_type + general + 全国)
    if industry_type != "general" or region != "全国":
        factor = query.filter(
            EmissionFactorItem.industry_type == "general",
            EmissionFactorItem.region == "全国"
        ).first()
        
        if factor:
            return _format_factor(factor)

    # 若全未命中，返回默认空结果
    return {"value": 0.0, "unit": "unknown", "source": "未找到匹配因子"}

def _format_factor(factor: EmissionFactorItem) -> dict:
    return {
        "value": factor.factor_value,
        "unit": factor.factor_unit,
        "source": f"{factor.source} ({factor.version})"
    }

class FactorStore:
    """策略层使用的查询器实例，封装 db_session 和当前上下文环境变量"""
    def __init__(self, db: Session, region: str = "全国", version: str = None):
        self.db = db
        self.region = region
        self.version = version
        
    def get_factor(self, activity_type: str, industry_type: str = "general") -> dict:
        """对接底层暴露的 get_factor 统一函数"""
        return get_factor(
            db=self.db, 
            activity_type=activity_type, 
            industry_type=industry_type, 
            region=self.region, 
            version=self.version
        )
