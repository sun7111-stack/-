"""上传-解析-活动链路核心表模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.sql import func

from database import Base


class RawDataRecord(Base):
    """原始凭证记录"""

    __tablename__ = "raw_data_record"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    enterprise_id = Column(Integer, ForeignKey("enterprise_profiles.id"), nullable=True, index=True)
    data_type = Column(String(50), nullable=False, default="", index=True)
    file_name = Column(String(255), nullable=False, default="")
    file_path = Column(String(500), nullable=False, default="")
    upload_time = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    parse_status = Column(String(30), nullable=False, default="pending", index=True)

    __table_args__ = (
        Index("idx_raw_enterprise_upload", "enterprise_id", "upload_time"),
        Index("idx_raw_status_upload", "parse_status", "upload_time"),
    )


class ParsedDataRecord(Base):
    """OCR/AI解析字段记录"""

    __tablename__ = "parsed_data_record"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    raw_data_id = Column(Integer, ForeignKey("raw_data_record.id"), nullable=False, index=True)
    raw_field_name = Column(String(120), nullable=False, default="")
    raw_field_value = Column(Text, nullable=False, default="")
    parsed_field_name = Column(String(120), nullable=False, default="")
    parsed_field_value = Column(Text, nullable=False, default="")
    confidence_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    __table_args__ = (
        Index("idx_parsed_raw_created", "raw_data_id", "created_at"),
    )


class ActivityRecord(Base):
    """标准化活动记录"""

    __tablename__ = "activity_record"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    enterprise_id = Column(Integer, ForeignKey("enterprise_profiles.id"), nullable=True, index=True)
    parsed_id = Column(Integer, ForeignKey("parsed_data_record.id"), nullable=False, index=True)
    activity_type = Column(String(80), nullable=False, default="", index=True)
    activity_amount = Column(Float, nullable=False, default=0.0)
    activity_unit = Column(String(40), nullable=False, default="")
    amount_raw = Column(Float, nullable=True, default=0.0)
    unit_raw = Column(String(40), nullable=False, default="")

    scope = Column(String(10), nullable=False, default="S3", index=True)
    scope3_category = Column(String(80), nullable=True, default="", index=True)
    stage = Column(String(40), nullable=False, default="production", index=True)
    dq_activity_level = Column(String(10), nullable=False, default="C")

    region_code = Column(String(30), nullable=False, default="全国", index=True)
    period_time = Column(String(30), nullable=False, default="", index=True)
    clean_status = Column(String(30), nullable=False, default="warning", index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    __table_args__ = (
        Index("idx_activity_enterprise_period", "enterprise_id", "period_time"),
        Index("idx_activity_status_created", "clean_status", "created_at"),
    )
