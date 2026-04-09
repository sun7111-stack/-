"""碳管理模块 Schemas"""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# ---------- 数据上传 ----------

class DataUploadCreate(BaseModel):
    file_name: str
    file_type: str = "invoice"
    category: str = "electricity"
    period: str = ""
    note: str = ""


class DataUploadOut(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_type: str
    file_size: int
    category: str
    status: str
    parsed_data: Optional[Any] = {}
    period: str
    note: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- 手动录入 ----------

class ManualEntryCreate(BaseModel):
    """手动录入能耗数据"""
    category: str = "electricity"
    value: float = 0.0
    unit: str = "kWh"
    period: str = ""
    note: str = ""


# ---------- 能耗分析 ----------

class EnergyItem(BaseModel):
    name: str
    name_cn: str
    value: float
    unit: str
    percentage: float
    trend: str = "down"


class EnergyAnalysis(BaseModel):
    total_energy: float
    total_emission: float
    items: List[EnergyItem]
    monthly_trend: List[dict]
    yoy_change: float
    suggestions: List[str]
