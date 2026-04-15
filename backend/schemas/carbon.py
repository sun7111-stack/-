"""碳排放相关的Pydantic模型"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ---------- 枚举定义：为团队联调提供强弱类型契约 ----------
class ShopTypeEnum(str, Enum):
    cross_border = "cross_border"
    daily_goods = "daily_goods"
    general = "general"

class ActivityTypeEnum(str, Enum):
    electricity = "electricity"
    natural_gas = "natural_gas"
    diesel = "diesel"
    waste = "waste"
    air_logistics = "air_logistics"
    warehouse_energy = "warehouse_energy"
    reverse_logistics = "reverse_logistics"
    packaging_waste = "packaging_waste"
    general_logistics = "general_logistics"

# ---------- 碳排放计算参数(适配OCR/VLM和分层引擎) ----------

class OCRCarbonCalcRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    # OCR 识别的原始类型及字段 (对接2号同学)
    doc_type: Optional[str] = Field(default="unknown", description="凭证类型：如电费单、物流面单")
    suggested_activity_type: Optional[ActivityTypeEnum] = Field(default=ActivityTypeEnum.electricity, description="建议的活动类型")
    # 约定：如果是电费单，必须有 amount(用电量)；如果是物流单，可传 distance, weight
    fields: Dict[str, Any] = Field(default_factory=dict, description="OCR识别出的具体字段，如 {'amount': 1245, 'unit': 'kWh'}")
    
    # 也可以直接传已合并好的多项活动数据
    activity_data: Optional[Dict[str, float]] = Field(default_factory=dict, description="活动数据聚合，如 {'electricity': 1000.0, 'diesel': 500.0}")

    # 场景上下文 (基础参数)
    shop_type: ShopTypeEnum = Field(default=ShopTypeEnum.general, description="店铺/企业类型")
    region: str = Field(default="全国", description="所在地区")
    annual_revenue: float = Field(default=1000.0, description="年营收(万元)，用于计算碳排放强度")
    period: Optional[str] = Field(default="", description="核算周期")
    model_version: str = Field(default="v2", description="核算模型版本: v1/v2")
    uncertainty_mode: str = Field(default="analytic", description="不确定性模式: analytic/mc")

class BreakdownItem(BaseModel):
    item: str
    amount: float
    factor: float
    emission: float
    unit: Optional[str] = ""
    source: Optional[str] = ""

class BenchmarkCompare(BaseModel):
    industry_avg: float
    deviation_ratio: float
    position: str
    rank_label: str
    carbon_intensity: Optional[float] = 0.0

class DynamicCarbonCalcResult(BaseModel):
    """动态策略策略核算返回结果"""
    model_config = ConfigDict(protected_namespaces=())

    record_id: Optional[int] = None
    total_emission: float
    breakdown: List[BreakdownItem]
    benchmark_compare: BenchmarkCompare
    carbon_flow: Optional[Dict[str, Any]] = None
    scope_breakdown: Optional[Dict[str, float]] = None
    uncertainty: Optional[Dict[str, Any]] = None
    top_contributors: Optional[List[Dict[str, Any]]] = None
    factor_trace: Optional[List[Dict[str, Any]]] = None
    model_version: Optional[str] = "v1"
    analysis_id: Optional[int] = None
    message: Optional[str] = "核算完成"


class CarbonResultV2Out(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    analysis_id: int
    model_version: str
    total_emission: float
    breakdown: List[Dict[str, Any]]
    scope_breakdown: Dict[str, float]
    benchmark_compare: Dict[str, Any]
    uncertainty: Dict[str, Any]
    top_contributors: List[Dict[str, Any]]
    factor_trace: List[Dict[str, Any]]


class CarbonFlowOut(BaseModel):
    analysis_id: int
    carbon_flow: Dict[str, Any]


class CarbonExplainOut(BaseModel):
    analysis_id: int
    explain_trace: Dict[str, Any]



# ---------- 排放因子 ----------

class EmissionFactorOut(BaseModel):
    id: int
    name: str
    name_cn: str
    factor: float
    unit: str
    source: str

    model_config = ConfigDict(from_attributes=True)


# ---------- 行业基准 ----------

class IndustryBenchmarkOut(BaseModel):
    id: int
    industry: str
    industry_cn: str
    carbon_per_revenue: float
    energy_metric: float
    other_metric: float

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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
