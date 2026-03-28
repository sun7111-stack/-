"""ESG评分相关模型"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class EsgScore(Base):
    """ESG评分记录表"""
    __tablename__ = "esg_scores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 三维度评分
    environment = Column(Float, default=0.0, comment="环境(E)得分")
    social = Column(Float, default=0.0, comment="社会(S)得分")
    governance = Column(Float, default=0.0, comment="治理(G)得分")
    total = Column(Float, default=0.0, comment="综合得分(E*0.4+S*0.3+G*0.3)")

    # 环境维度详细输入
    env_electricity_usage = Column(Float, default=0.0)
    env_gas_usage = Column(Float, default=0.0)
    env_fuel_usage = Column(Float, default=0.0)
    env_waste_generation = Column(Float, default=0.0)
    env_recycling_rate = Column(Float, default=0.0)

    # 社会维度详细输入
    soc_employee_satisfaction = Column(Float, default=75.0)
    soc_training_hours = Column(Float, default=20.0)
    soc_turnover_rate = Column(Float, default=15.0)
    soc_community_investment = Column(Float, default=50.0)
    soc_supplier_esg = Column(Float, default=60.0)
    soc_customer_satisfaction = Column(Float, default=85.0)
    soc_complaint_rate = Column(Float, default=2.0)

    # 治理维度详细输入
    gov_governance_level = Column(Float, default=60.0)
    gov_independent_directors = Column(Float, default=30.0)
    gov_female_directors = Column(Float, default=25.0)
    gov_compliance_training = Column(Float, default=4.0)
    gov_anti_corruption = Column(Float, default=60.0)
    gov_esg_disclosure = Column(Float, default=60.0)
    gov_audit_independence = Column(Float, default=50.0)
    gov_risk_management = Column(Float, default=60.0)
    gov_data_security = Column(Float, default=50.0)

    # 改进建议JSON
    recommendations = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    user = relationship("User", back_populates="esg_scores")
