"""碳排放相关的Pydantic模型"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---------- 排放因子 ----------

class EmissionFactorOut(BaseModel):
    id: int
    name: str
    name_cn: str
    factor: float
    unit: str
    source: str

    class Config:
        from_attributes = True


# ---------- 行业基准 ----------

class IndustryBenchmarkOut(BaseModel):
    id: int
    industry: str
    industry_cn: str
    carbon_per_revenue: float
    energy_metric: float
    other_metric: float

    class Config:
        from_attributes = True


# ---------- 碳核算记录 ----------

class CarbonRecordCreate(BaseModel):
    company_type: Optional[str] = "ecommerce"
    annual_revenue: Optional[float] = 1000.0
    electricity_usage: Optional[float] = 0.0
    gas_usage: Optional[float] = 0.0
    fuel_usage: Optional[float] = 0.0
    waste_generation: Optional[float] = 0.0
    recycling_rate: Optional[float] = 0.0
    period: Optional[str] = ""
    note: Optional[str] = ""


class CarbonRecordOut(BaseModel):
    id: int
    user_id: int
    company_type: str
    annual_revenue: float
    electricity_usage: float
    gas_usage: float
    fuel_usage: float
    waste_generation: float
    recycling_rate: float
    total_emission: float
    carbon_intensity: float
    period: str
    note: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CarbonCalcResult(BaseModel):
    """碳核算返回结果"""
    record_id: int
    total_emission: float
    carbon_intensity: float
    industry_benchmark: float
    recycling_rate: float
    env_score: int
    level: str
    message: str
