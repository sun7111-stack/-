"""碳核算V2结果快照模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func

from database import Base


class AnalysisResultV2Snapshot(Base):
    __tablename__ = "analysis_result_v2_snapshot"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False, unique=True, index=True)

    model_version = Column(String(10), nullable=False, default="v2")
    uncertainty_mode = Column(String(20), nullable=False, default="analytic")

    scope_breakdown = Column(JSON, nullable=False, default=dict)
    source_breakdown = Column(JSON, nullable=False, default=list)
    uncertainty = Column(JSON, nullable=False, default=dict)
    top_contributors = Column(JSON, nullable=False, default=list)
    factor_trace = Column(JSON, nullable=False, default=list)
    carbon_flow_graph = Column(JSON, nullable=False, default=dict)
    explain_trace = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
