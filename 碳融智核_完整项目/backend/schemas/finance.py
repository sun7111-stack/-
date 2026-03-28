"""金融产品相关的Pydantic模型"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FinancialProductOut(BaseModel):
    id: int
    name: str
    product_type: str
    bank: str
    interest_rate: str
    max_amount: float
    term: str
    requirements: str
    description: str
    popularity: int
    category: str

    class Config:
        from_attributes = True


class FinanceApplicationCreate(BaseModel):
    product_id: int
    amount: float
    purpose: str


class FinanceApplicationOut(BaseModel):
    id: int
    user_id: int
    product_id: int
    amount: float
    purpose: str
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
