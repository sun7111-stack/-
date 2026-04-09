"""用户相关的Pydantic模型"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ---------- 请求模型 ----------

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    company: Optional[str] = ""
    company_type: Optional[str] = "ecommerce"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PhoneLoginRequest(BaseModel):
    """手机号 + 短信验证码登录（自动注册）"""
    phone: str
    sms_code: str


class SendSmsRequest(BaseModel):
    """发送短信验证码（需先通过图形验证码）"""
    phone: str
    captcha_id: str
    captcha: str


class EnterpriseLoginRequest(BaseModel):
    """企业账号 + 密码登录"""
    account: str
    password: str


# ---------- 响应模型 ----------

class UserInfo(BaseModel):
    id: int
    email: Optional[str] = None
    phone: Optional[str] = None
    enterprise_account: Optional[str] = None
    name: str
    company: str
    company_type: str
    position: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class CaptchaResponse(BaseModel):
    captcha_id: str
    captcha_image: str  # data:image/svg+xml;base64,...


class SmsCodeResponse(BaseModel):
    success: bool
    message: str
    code: Optional[str] = None  # 仅开发环境返回


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    company_type: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
