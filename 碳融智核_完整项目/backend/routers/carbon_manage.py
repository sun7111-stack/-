"""碳管理模块路由 - 数据上传 / 碳核算 / 能耗分析 / 排放因子库"""
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.data_upload import DataUpload
from models.carbon import CarbonRecord, EmissionFactor
from schemas.carbon_manage import (
    DataUploadCreate,
    DataUploadOut,
    ManualEntryCreate,
    EnergyAnalysis,
    EnergyItem,
)
from utils.auth import get_current_user

router = APIRouter(prefix="/api/carbon-manage", tags=["碳管理"])


# ============================================================
# 数据上传
# ============================================================

@router.get("/uploads", response_model=List[DataUploadOut], summary="获取上传记录")
def list_uploads(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(DataUpload)
        .filter(DataUpload.user_id == current_user.id)
        .order_by(DataUpload.created_at.desc())
        .limit(limit)
        .all()
    )
    return records


@router.post("/upload", response_model=DataUploadOut, summary="上传数据文件")
def upload_data(
    body: DataUploadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """模拟文件上传并解析（实际项目应接入文件存储和OCR/解析服务）"""
    # 模拟解析结果
    parsed = _simulate_parse(body.category, body.file_name)

    record = DataUpload(
        user_id=current_user.id,
        file_name=body.file_name,
        file_type=body.file_type,
        file_size=0,
        category=body.category,
        status="parsed",
        parsed_data=parsed,
        period=body.period or datetime.now().strftime("%Y-%m"),
        note=body.note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/uploads/{upload_id}", summary="删除上传记录")
def delete_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(DataUpload)
        .filter(DataUpload.id == upload_id, DataUpload.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"success": True, "message": "已删除"}


# ============================================================
# 手动录入
# ============================================================

@router.post("/manual-entry", response_model=DataUploadOut, summary="手动录入数据")
def manual_entry(
    body: ManualEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = DataUpload(
        user_id=current_user.id,
        file_name=f"手动录入-{body.category}",
        file_type="manual",
        file_size=0,
        category=body.category,
        status="parsed",
        parsed_data={"value": body.value, "unit": body.unit},
        period=body.period or datetime.now().strftime("%Y-%m"),
        note=body.note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ============================================================
# 能耗分析
# ============================================================

@router.get("/energy-analysis", response_model=EnergyAnalysis, summary="能耗分析")
def get_energy_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据用户碳核算记录聚合能耗分析数据"""
    records = (
        db.query(CarbonRecord)
        .filter(CarbonRecord.user_id == current_user.id)
        .order_by(CarbonRecord.created_at.desc())
        .limit(12)
        .all()
    )

    factors = {f.name: f for f in db.query(EmissionFactor).all()}

    if records:
        latest = records[0]
        elec = latest.electricity_usage
        gas = latest.gas_usage
        fuel = latest.fuel_usage
        total_e = elec + gas * 10.5 + fuel * 9.8  # 换算为kWh等效
    else:
        elec, gas, fuel = 12450, 850, 320
        total_e = elec + gas * 10.5 + fuel * 9.8

    total_emission = (
        elec * factors.get("electricity", type("", (), {"factor": 0.581})).factor
        + gas * factors.get("natural_gas", type("", (), {"factor": 1.89})).factor
        + fuel * factors.get("diesel", type("", (), {"factor": 2.68})).factor
    )

    elec_pct = round(elec / total_e * 100, 1) if total_e else 0
    gas_pct = round(gas * 10.5 / total_e * 100, 1) if total_e else 0
    fuel_pct = round(fuel * 9.8 / total_e * 100, 1) if total_e else 0

    items = [
        EnergyItem(name="electricity", name_cn="电力", value=elec, unit="kWh", percentage=elec_pct, trend="down"),
        EnergyItem(name="natural_gas", name_cn="天然气", value=gas, unit="m³", percentage=gas_pct, trend="stable"),
        EnergyItem(name="fuel", name_cn="燃油(柴油)", value=fuel, unit="L", percentage=fuel_pct, trend="down"),
    ]

    monthly_trend = [
        {"month": "1月", "electricity": 1380, "gas": 95, "fuel": 38},
        {"month": "2月", "electricity": 1290, "gas": 88, "fuel": 35},
        {"month": "3月", "electricity": 1210, "gas": 82, "fuel": 32},
        {"month": "4月", "electricity": 1150, "gas": 78, "fuel": 30},
    ]

    return EnergyAnalysis(
        total_energy=round(total_e, 1),
        total_emission=round(total_emission, 1),
        items=items,
        monthly_trend=monthly_trend,
        yoy_change=-8.5,
        suggestions=[
            "电力能耗占比最高，建议增加光伏发电比例",
            "燃油消耗同比下降12%，可继续推广电动叉车",
            "建议安装能耗监测系统实现实时管控",
        ],
    )


# ============================================================
# 辅助函数
# ============================================================

def _simulate_parse(category: str, file_name: str) -> dict:
    """模拟文件解析结果"""
    templates = {
        "electricity": {"value": 1245, "unit": "kWh", "cost": 1245.00, "type": "工商业用电"},
        "gas": {"value": 85, "unit": "m³", "cost": 340.00, "type": "天然气"},
        "fuel": {"value": 45.6, "unit": "L", "cost": 386.52, "type": "柴油"},
        "water": {"value": 120, "unit": "m³", "cost": 480.00, "type": "工业用水"},
        "waste": {"value": 500, "unit": "kg", "cost": 0, "type": "一般固废"},
    }
    return templates.get(category, {"value": 0, "unit": "", "type": "未知"})
