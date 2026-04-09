"""驾驶舱模块 Schemas"""
from pydantic import BaseModel
from typing import Optional, List


class EmissionPoint(BaseModel):
    month: str
    emission: float


class EmissionMonitor(BaseModel):
    """碳排放监控数据"""
    title: str = "碳排放监控"
    unit: str = "t"
    data: List[EmissionPoint]
    total: float
    yoy_change: float
    trend: str = "down"


class EnergyStructureItem(BaseModel):
    name: str
    value: float
    percentage: float
    unit: str
    color: str = ""


class EnergyStructure(BaseModel):
    """能耗结构"""
    title: str = "能耗结构"
    items: List[EnergyStructureItem]
    total_kwh: float


class EsgBoardItem(BaseModel):
    dimension: str
    score: float
    change: float
    trend: str = "up"


class EsgBoard(BaseModel):
    """ESG看板"""
    total_score: float
    level: str
    dimensions: List[EsgBoardItem]
    industry_rank: str
    percentile: float


class KeyIndicator(BaseModel):
    name: str
    value: str
    unit: str
    trend: str = "up"
    change: str = ""
    icon: str = ""


class KeyIndicators(BaseModel):
    """关键指标"""
    indicators: List[KeyIndicator]
