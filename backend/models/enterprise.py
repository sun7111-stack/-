"""企业中心模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class EnterpriseProfile(Base):
    """企业基本信息（每个用户/企业一条记录）"""
    __tablename__ = "enterprise_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    # 基本信息
    company_name = Column(String(200), nullable=False, default="")
    industry = Column(String(100), default="")           # 行业：金属制品、电子商务等
    company_scale = Column(String(20), default="")       # 企业规模：micro/small/medium/large
    annual_revenue = Column(Float, default=0)             # 年营收（万元）
    employee_count = Column(Integer, default=0)           # 员工数
    main_products = Column(String(500), default="")       # 主要产品
    address = Column(String(500), default="")             # 企业地址
    legal_person = Column(String(50), default="")         # 法人代表
    established_date = Column(String(20), default="")     # 成立日期
    credit_code = Column(String(50), default="")          # 统一社会信用代码
    contact_person = Column(String(50), default="")       # 联系人
    contact_phone = Column(String(20), default="")        # 联系电话

    # 碳排放统计
    total_carbon_emission = Column(Float, default=0)      # 总碳排放量（吨）
    logistics_carbon_intensity = Column(Float, default=0)  # 物流碳强度
    energy_intensity = Column(Float, default=0)           # 能耗强度

    # ESG
    esg_score = Column(Float, default=0)                  # ESG综合得分
    carbon_efficiency_grade = Column(String(10), default="")  # 碳效等级：A+, A, B+, B, C...

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", backref="enterprise_profile")
    certifications = relationship("EnterpriseCertification", back_populates="enterprise", cascade="all, delete-orphan")
    activities = relationship("EnterpriseActivity", back_populates="enterprise", cascade="all, delete-orphan")


class EnterpriseCertification(Base):
    """企业资质认证"""
    __tablename__ = "enterprise_certifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    enterprise_id = Column(Integer, ForeignKey("enterprise_profiles.id"), nullable=False, index=True)

    cert_name = Column(String(200), nullable=False)          # 认证名称
    cert_type = Column(String(50), default="")               # 类型：iso, green, esg, other
    cert_number = Column(String(100), default="")            # 证书编号
    issuing_authority = Column(String(200), default="")      # 发证机构
    issue_date = Column(String(20), default="")              # 发证日期
    expiry_date = Column(String(20), default="")             # 到期日期
    status = Column(String(20), default="valid")             # valid / expired / pending
    description = Column(Text, default="")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    enterprise = relationship("EnterpriseProfile", back_populates="certifications")


class EnterpriseActivity(Base):
    """企业最近活动"""
    __tablename__ = "enterprise_activities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    enterprise_id = Column(Integer, ForeignKey("enterprise_profiles.id"), nullable=False, index=True)

    action = Column(String(50), nullable=False)       # 动作类型：login, upload, report, finance, esg, edit
    title = Column(String(200), nullable=False)       # 活动标题
    detail = Column(Text, default="")                 # 活动详情
    ip_address = Column(String(50), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    enterprise = relationship("EnterpriseProfile", back_populates="activities")
