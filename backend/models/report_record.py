"""报告导出与追溯记录模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func

from database import Base


class ReportRecord(Base):
    __tablename__ = "report_records"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    analysis_id = Column(String(64), nullable=False, default="", index=True)
    report_type = Column(String(50), nullable=False, default="basic")
    report_title = Column(String(200), nullable=False, default="")
    generate_time = Column(DateTime, nullable=False, server_default=func.now())
    export_status = Column(String(30), nullable=False, default="pending", index=True)
    file_path = Column(String(300), nullable=False, default="")
    report_context = Column(JSON, nullable=False, default=dict)
    report_preview = Column(JSON, nullable=False, default=dict)
