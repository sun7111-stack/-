"""因子匹配日志模型（可解释与可复现）"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from database import Base


class FactorMatchLog(Base):
    __tablename__ = "factor_match_log"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False, index=True)
    activity_id = Column(Integer, nullable=True, index=True)
    factor_id = Column(Integer, nullable=True, index=True)

    match_rule = Column(String(100), nullable=False, default="")
    fallback_level = Column(String(50), nullable=False, default="")
    match_explain = Column(Text, nullable=False, default="")

    factor_value_snapshot = Column(Float, nullable=False, default=0.0)
    factor_source_snapshot = Column(String(255), nullable=False, default="")

    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
