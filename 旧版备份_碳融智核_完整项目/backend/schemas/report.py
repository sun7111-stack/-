"""报告及其他相关的Pydantic模型"""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class ReportGenerate(BaseModel):
    template_type: str  # basic / esg / finance
    scenario: Optional[str] = ""  # 绿色信贷/政府补贴/内部管理/合规披露
    title: Optional[str] = ""


class ReportOut(BaseModel):
    id: int
    user_id: int
    report_no: str
    template_type: str
    title: str
    word_count: int
    charts_count: int
    generation_time: int
    scenario: Optional[str] = ""
    status: str
    review_comment: Optional[str] = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportReview(BaseModel):
    status: str  # approved / rejected
    comment: str = ""


class CustomTemplate(BaseModel):
    name: str
    description: str = ""
    sections: List[str] = []
    scenario: str = ""


class PolicyOut(BaseModel):
    id: int
    title: str
    agency: str
    publish_date: str
    summary: str
    relevance: str

    class Config:
        from_attributes = True


class CaseStudyOut(BaseModel):
    id: int
    company: str
    industry: str
    challenge: str
    solution: str
    results: Any
    testimonial: str

    class Config:
        from_attributes = True


class ContactMessageCreate(BaseModel):
    name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    company: Optional[str] = ""
    company_type: Optional[str] = ""  # ecommerce/manufacture/logistics/other
    message: str
    msg_type: Optional[str] = "consult"


class ContactMessageOut(BaseModel):
    id: int
    name: str
    email: str
    message: str
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApiResponse(BaseModel):
    """通用API响应"""
    success: bool = True
    message: str = ""
    data: Optional[Any] = None
