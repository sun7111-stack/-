"""数据上传 & 申请材料 模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class DataUpload(Base):
    """数据上传记录（碳管理模块）"""
    __tablename__ = "data_uploads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_name = Column(String(200), nullable=False, comment="文件名")
    file_type = Column(String(50), default="", comment="文件类型: invoice/bill/system/manual")
    file_size = Column(Integer, default=0, comment="文件大小(bytes)")
    category = Column(String(50), default="", comment="数据类别: electricity/gas/fuel/water/waste")
    status = Column(String(20), default="parsed", comment="状态: pending/parsed/error")
    parsed_data = Column(JSON, default=dict, comment="解析后的数据")
    period = Column(String(20), default="", comment="所属期间")
    note = Column(Text, default="", comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="data_uploads")


class ApplicationMaterial(Base):
    """金融申请材料"""
    __tablename__ = "application_materials"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_name = Column(String(200), nullable=False, comment="文件名")
    file_type = Column(String(50), default="", comment="文件类型: pdf/xlsx/doc/image")
    doc_category = Column(String(50), default="", comment="材料类别: license/financial/esg/other")
    status = Column(String(20), default="uploaded", comment="审核状态: uploaded/verified/rejected")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="application_materials")
