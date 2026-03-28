"""报告与联系相关模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Report(Base):
    """报告记录表"""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    report_no = Column(String(50), unique=True, nullable=False, comment="报告编号")
    template_type = Column(
        Enum("basic", "reduction", "esg", "finance", name="template_type_enum"),
        default="basic",
        comment="模板类型"
    )
    title = Column(String(200), default="", comment="报告标题")
    content = Column(JSON, default=dict, comment="报告内容(JSON)")
    word_count = Column(Integer, default=0, comment="字数")
    charts_count = Column(Integer, default=0, comment="图表数")
    generation_time = Column(Integer, default=0, comment="生成耗时(秒)")
    scenario = Column(String(100), default="", comment="使用场景: 绿色信贷/政府补贴/内部管理/合规披露")
    status = Column(
        Enum("draft", "generating", "completed", "exported", "reviewing", "approved", name="report_status_enum"),
        default="draft",
    )
    review_comment = Column(Text, default="", comment="审核意见")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    user = relationship("User", back_populates="reports")


class Policy(Base):
    """政策法规表"""
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="政策标题")
    agency = Column(String(100), default="", comment="发布机构")
    publish_date = Column(String(20), default="", comment="发布日期")
    summary = Column(Text, default="", comment="摘要")
    relevance = Column(String(20), default="medium", comment="关联度 high/medium/low")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CaseStudy(Base):
    """客户案例表"""
    __tablename__ = "case_studies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company = Column(String(100), nullable=False, comment="企业名称")
    industry = Column(String(50), default="", comment="行业")
    challenge = Column(Text, default="", comment="挑战")
    solution = Column(Text, default="", comment="解决方案")
    results = Column(JSON, default=dict, comment="成效数据JSON")
    testimonial = Column(Text, default="", comment="客户评价")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ContactMessage(Base):
    """联系我们/咨询消息表"""
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(50), default="")
    email = Column(String(100), default="")
    phone = Column(String(20), default="")
    company = Column(String(100), default="")
    company_type = Column(String(50), default="", comment="企业类型: ecommerce/manufacture/logistics/other")
    message = Column(Text, default="")
    msg_type = Column(String(20), default="consult", comment="类型: consult/feedback/complaint")
    status = Column(String(20), default="pending", comment="处理状态")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    user = relationship("User", back_populates="contacts")
