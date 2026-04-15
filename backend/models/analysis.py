"""核算结果与风控结果模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    enterprise_name = Column(String(200), nullable=False, default="")
    analysis_time = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    total_emission = Column(Float, nullable=False, default=0.0)
    carbon_intensity = Column(Float, nullable=False, default=0.0)
    industry_deviation = Column(Float, nullable=False, default=0.0)
    scope1 = Column(Float, nullable=False, default=0.0)
    scope2 = Column(Float, nullable=False, default=0.0)
    scope3 = Column(Float, nullable=False, default=0.0)
    ci95_low = Column(Float, nullable=False, default=0.0)
    ci95_high = Column(Float, nullable=False, default=0.0)
    uncertainty_mode = Column(String(20), nullable=False, default="analytic")
    risk_level = Column(String(30), nullable=False, default="medium")
    major_source = Column(String(100), nullable=False, default="")
    top_contributor_activity_id = Column(Integer, nullable=True)
    advice_text = Column(Text, nullable=False, default="")


class AnalysisBreakdown(Base):
    __tablename__ = "analysis_breakdowns"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False, index=True)
    source_type = Column(String(80), nullable=False, default="")
    emission_value = Column(Float, nullable=False, default=0.0)
    proportion = Column(Float, nullable=False, default=0.0)


class RiskResult(Base):
    __tablename__ = "risk_results"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    analysis_id = Column(Integer, nullable=True, index=True)
    risk_score = Column(Float, nullable=False, default=0.0)
    risk_level = Column(String(30), nullable=False, default="medium")
    risk_reason = Column(Text, nullable=False, default="")
    risk_advice = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
