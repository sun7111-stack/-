"""ESG评分相关的Pydantic模型"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class EsgEnvironmentInput(BaseModel):
    """环境维度输入"""
    company_type: Optional[str] = "ecommerce"
    annual_revenue: Optional[float] = 1000.0
    electricity_usage: Optional[float] = 0.0
    gas_usage: Optional[float] = 0.0
    fuel_usage: Optional[float] = 0.0
    waste_generation: Optional[float] = 0.0
    recycling_rate: Optional[float] = 0.0


class EsgSocialInput(BaseModel):
    """社会维度输入"""
    employee_scale: Optional[str] = "medium"  # small/medium/large
    employee_satisfaction: Optional[float] = 75.0
    training_hours: Optional[float] = 20.0
    turnover_rate: Optional[float] = 15.0
    community_investment: Optional[float] = 50.0
    supplier_esg: Optional[float] = 60.0
    customer_satisfaction: Optional[float] = 85.0
    complaint_rate: Optional[float] = 2.0


class EsgGovernanceInput(BaseModel):
    """治理维度输入"""
    ownership_type: Optional[str] = "private"  # private/state/foreign/joint
    governance_level: Optional[float] = 60.0
    independent_directors: Optional[float] = 30.0
    female_directors: Optional[float] = 25.0
    compliance_training: Optional[float] = 4.0
    anti_corruption: Optional[float] = 60.0
    esg_disclosure: Optional[float] = 60.0
    audit_independence: Optional[float] = 50.0
    risk_management: Optional[float] = 60.0
    data_security: Optional[float] = 50.0


class EsgFullInput(BaseModel):
    """完整ESG输入（综合评估）"""
    environment: EsgEnvironmentInput
    social: EsgSocialInput
    governance: EsgGovernanceInput


class EsgScoreOut(BaseModel):
    """ESG评分输出"""
    id: int
    user_id: int
    environment: float
    social: float
    governance: float
    total: float
    recommendations: Optional[List[str]] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EsgDimensionResult(BaseModel):
    """单维度计算结果"""
    score: int
    level: str
    message: str
    details: dict


class EsgTotalResult(BaseModel):
    """综合ESG计算结果"""
    record_id: int
    environment: int
    social: int
    governance: int
    total: int
    level: str
    recommendations: List[str]
