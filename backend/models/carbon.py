"""碳排放相关模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class EmissionFactor(Base):
    """排放因子表"""
    __tablename__ = "emission_factors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment="排放源名称")
    name_cn = Column(String(50), default="", comment="中文名称")
    factor = Column(Float, nullable=False, comment="排放因子值")
    unit = Column(String(50), default="", comment="单位说明，如 kgCO2/kWh")
    source = Column(String(100), default="", comment="数据来源")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class EmissionFactorItem(Base):
    """(新增)详细排放因子表-轻量级参数关联数据库"""
    __tablename__ = "emission_factor_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    activity_type = Column(String(50), nullable=False, index=True, comment="活动类型(如electricity, natural_gas, air_logistics等)")
    industry_type = Column(String(50), default="general", index=True, comment="行业或场景类型(如cross_border, general等)")
    region = Column(String(50), default="全国", index=True, comment="适用地区(如全国, 华中, 华东)")
    factor_value = Column(Float, nullable=False, comment="排放因子值")
    factor_unit = Column(String(50), nullable=False, comment="单位(如kgCO2e/kWh, kgCO2e/ton-km)")
    source = Column(String(200), default="", comment="因子来源(用于可追溯性)")
    version = Column(String(50), default="2025-demo", index=True, comment="版本(如2025-demo, CN-grid-2025)")
    description = Column(Text, default="", comment="描述及备注")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class IndustryBenchmark(Base):
    """行业基准数据表"""
    __tablename__ = "industry_benchmarks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    industry = Column(String(50), unique=True, nullable=False, comment="行业标识")
    industry_cn = Column(String(50), default="", comment="行业中文名")
    carbon_per_revenue = Column(Float, default=0.0, comment="碳排放强度(t/万元)")
    energy_metric = Column(Float, default=0.0, comment="能耗指标")
    other_metric = Column(Float, default=0.0, comment="其他指标(如包装率、废弃率等)")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CarbonRecord(Base):
    """碳排放记录表"""
    __tablename__ = "carbon_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company_type = Column(String(50), default="")
    annual_revenue = Column(Float, default=0.0, comment="年营收(万元)")

    # 能源消耗数据
    electricity_usage = Column(Float, default=0.0, comment="用电量(kWh)")
    gas_usage = Column(Float, default=0.0, comment="天然气用量(m³)")
    fuel_usage = Column(Float, default=0.0, comment="燃油用量(L)")
    waste_generation = Column(Float, default=0.0, comment="废弃物产生量(kg)")
    recycling_rate = Column(Float, default=0.0, comment="回收利用率(%)")

    # 计算结果
    total_emission = Column(Float, default=0.0, comment="总碳排放量(kgCO2)")
    carbon_intensity = Column(Float, default=0.0, comment="碳排放强度(t/万元)")

    period = Column(String(20), default="", comment="核算周期，如 2024-Q1")
    note = Column(Text, default="", comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    user = relationship("User", back_populates="carbon_records")
