"""企业中心相关Pydantic模型"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ========== 企业基本信息 ==========

class EnterpriseProfileBase(BaseModel):
    company_name: str = ""
    industry: str = ""
    company_scale: str = ""            # 企业规模：micro/small/medium/large
    annual_revenue: float = 0          # 万元
    employee_count: int = 0
    main_products: str = ""
    address: str = ""
    legal_person: str = ""
    established_date: str = ""
    credit_code: str = ""
    contact_person: str = ""
    contact_phone: str = ""


class EnterpriseProfileUpdate(BaseModel):
    """更新企业信息（所有字段可选）"""
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_scale: Optional[str] = None
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    main_products: Optional[str] = None
    address: Optional[str] = None
    legal_person: Optional[str] = None
    established_date: Optional[str] = None
    credit_code: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None


class EnterpriseProfileResponse(EnterpriseProfileBase):
    id: int
    user_id: int
    total_carbon_emission: float = 0
    logistics_carbon_intensity: float = 0
    energy_intensity: float = 0
    esg_score: float = 0
    carbon_efficiency_grade: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 企业概览面板 ==========

class EnterpriseDashboard(BaseModel):
    """企业中心仪表盘数据"""
    company_name: str
    annual_revenue: float               # 万元
    annual_revenue_display: str          # "1.2亿" 这样的显示文本
    total_carbon_emission: float         # 吨
    esg_score: float
    carbon_efficiency_grade: str         # A+ / A / B+ / B / C
    logistics_carbon_intensity: float
    energy_intensity: float
    industry: str
    employee_count: int
    main_products: str


# ========== 资质认证 ==========

class CertificationCreate(BaseModel):
    cert_name: str
    cert_type: str = ""
    cert_number: str = ""
    issuing_authority: str = ""
    issue_date: str = ""
    expiry_date: str = ""
    status: str = "valid"
    description: str = ""


class CertificationUpdate(BaseModel):
    cert_name: Optional[str] = None
    cert_type: Optional[str] = None
    cert_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class CertificationResponse(BaseModel):
    id: int
    cert_name: str
    cert_type: str
    cert_number: str
    issuing_authority: str
    issue_date: str
    expiry_date: str
    status: str
    description: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 最近活动 ==========

class ActivityResponse(BaseModel):
    id: int
    action: str
    title: str
    detail: str
    ip_address: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 账号设置 ==========

class AccountSettingsUpdate(BaseModel):
    """账号设置更新"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    position: Optional[str] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = None


class AccountSettingsResponse(BaseModel):
    """账号信息"""
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    enterprise_account: Optional[str] = None
    company: str
    company_type: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 数据权限 ==========

class DataPermissionResponse(BaseModel):
    """数据权限信息"""
    can_view_carbon: bool = True
    can_edit_carbon: bool = True
    can_view_esg: bool = True
    can_edit_esg: bool = True
    can_generate_report: bool = True
    can_apply_finance: bool = True
    can_manage_users: bool = False
    role: str = "admin"
    data_scope: str = "all"
