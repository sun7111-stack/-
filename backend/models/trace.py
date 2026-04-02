"""数据确权留痕模型"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func

from database import Base


class DataTraceRecord(Base):
    """识别/结构化数据哈希留痕记录"""

    __tablename__ = "data_trace_records"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    bill_id = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    doc_type = Column(String(32), nullable=False)
    data_hash = Column(String(64), nullable=False, unique=True)
    raw_text = Column(Text, nullable=False)
    structured_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
