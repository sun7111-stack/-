"""金融产品相关模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class FinancialProduct(Base):
    """金融产品表"""
    __tablename__ = "financial_products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="产品名称")
    product_type = Column(String(50), default="", comment="产品类型 credit/supplychain/project等")
    bank = Column(String(100), default="", comment="合作银行")
    interest_rate = Column(String(50), default="", comment="利率说明")
    max_amount = Column(Float, default=0.0, comment="最大额度")
    term = Column(String(50), default="", comment="期限")
    requirements = Column(Text, default="", comment="申请条件")
    description = Column(Text, default="", comment="产品描述")
    popularity = Column(Integer, default=0, comment="热度")
    category = Column(String(20), default="", comment="分类标签: hot/recommended/new")
    is_active = Column(Integer, default=1, comment="是否上架")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    applications = relationship("FinanceApplication", back_populates="product")


class FinanceApplication(Base):
    """金融产品申请记录表"""
    __tablename__ = "finance_applications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("financial_products.id"), nullable=False)
    amount = Column(Float, default=0.0, comment="申请金额")
    purpose = Column(Text, default="", comment="用途说明")
    status = Column(
        Enum("pending", "reviewing", "approved", "rejected", name="application_status_enum"),
        default="pending",
        comment="审批状态"
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="finance_applications")
    product = relationship("FinancialProduct", back_populates="applications")
