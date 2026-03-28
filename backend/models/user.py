"""用户模型"""
from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(50), nullable=False)
    company = Column(String(100), default="")
    company_type = Column(
        Enum("ecommerce", "manufacture", "logistics", "service", name="company_type_enum"),
        default="ecommerce",
    )

    # ---- 个人信息 ----
    position = Column(String(100), default="")         # 职位

    # ---- 手机号登录 ----
    phone = Column(String(20), unique=True, nullable=True, index=True)

    # ---- 企业账号登录 ----
    enterprise_account = Column(String(100), unique=True, nullable=True, index=True)

    # ---- 登录安全：失败锁定 ----
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    esg_scores = relationship("EsgScore", back_populates="user", cascade="all, delete-orphan")
    carbon_records = relationship("CarbonRecord", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    finance_applications = relationship("FinanceApplication", back_populates="user", cascade="all, delete-orphan")
    contacts = relationship("ContactMessage", back_populates="user")
