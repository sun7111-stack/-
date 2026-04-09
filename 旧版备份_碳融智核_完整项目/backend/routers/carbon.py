"""碳排放核算路由"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.carbon import EmissionFactor, IndustryBenchmark, CarbonRecord
from schemas.carbon import (
    EmissionFactorOut,
    IndustryBenchmarkOut,
    CarbonRecordCreate,
    CarbonRecordOut,
    CarbonCalcResult,
)
from utils.auth import get_current_user
from utils.calculator import calculate_env_score

router = APIRouter(prefix="/api/carbon", tags=["碳排放核算"])


# ========== 公开接口（无需登录） ==========

@router.get("/emission-factors", response_model=List[EmissionFactorOut], summary="获取排放因子列表")
def list_emission_factors(db: Session = Depends(get_db)):
    return db.query(EmissionFactor).all()


@router.get("/industry-benchmarks", response_model=List[IndustryBenchmarkOut], summary="获取行业基准数据")
def list_industry_benchmarks(db: Session = Depends(get_db)):
    return db.query(IndustryBenchmark).all()


# ========== 需要登录的接口 ==========

@router.get("/records", response_model=List[CarbonRecordOut], summary="获取碳核算记录")
def list_carbon_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(CarbonRecord)
        .filter(CarbonRecord.user_id == current_user.id)
        .order_by(CarbonRecord.created_at.desc())
        .all()
    )
    return records


@router.post("/calculate", response_model=CarbonCalcResult, summary="执行碳核算并保存记录")
def calculate_carbon(
    body: CarbonRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 查询排放因子
    factors_rows = db.query(EmissionFactor).all()
    factors_dict = {f.name: f.factor for f in factors_rows}
    if not factors_dict:
        # 使用默认值（与前端一致）
        factors_dict = {
            "electricity": 0.581,
            "natural_gas": 1.89,
            "diesel": 2.68,
        }

    # 查询行业基准
    benchmarks_rows = db.query(IndustryBenchmark).all()
    benchmarks_dict = {
        b.industry: {
            "carbon_per_revenue": b.carbon_per_revenue,
            "energy_metric": b.energy_metric,
            "other_metric": b.other_metric,
        }
        for b in benchmarks_rows
    }
    if not benchmarks_dict:
        benchmarks_dict = {
            "ecommerce": {"carbon_per_revenue": 0.15, "energy_metric": 0.8, "other_metric": 0.65},
            "manufacture": {"carbon_per_revenue": 0.85, "energy_metric": 1.2, "other_metric": 0.25},
            "logistics": {"carbon_per_revenue": 0.45, "energy_metric": 0.12, "other_metric": 0.75},
            "service": {"carbon_per_revenue": 0.08, "energy_metric": 0.3, "other_metric": 0.9},
        }

    # 计算
    result = calculate_env_score(
        company_type=body.company_type,
        annual_revenue=body.annual_revenue,
        electricity_usage=body.electricity_usage,
        gas_usage=body.gas_usage,
        fuel_usage=body.fuel_usage,
        waste_generation=body.waste_generation,
        recycling_rate=body.recycling_rate,
        emission_factors=factors_dict,
        industry_benchmarks=benchmarks_dict,
    )

    # 保存记录
    record = CarbonRecord(
        user_id=current_user.id,
        company_type=body.company_type,
        annual_revenue=body.annual_revenue,
        electricity_usage=body.electricity_usage,
        gas_usage=body.gas_usage,
        fuel_usage=body.fuel_usage,
        waste_generation=body.waste_generation,
        recycling_rate=body.recycling_rate,
        total_emission=result["total_emission"],
        carbon_intensity=result["carbon_intensity"],
        period=body.period,
        note=body.note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return CarbonCalcResult(
        record_id=record.id,
        total_emission=result["total_emission"],
        carbon_intensity=result["carbon_intensity"],
        industry_benchmark=result["industry_benchmark"],
        recycling_rate=result["recycling_rate"],
        env_score=result["score"],
        level=result["level"],
        message=result["message"],
    )


@router.get("/records/{record_id}", response_model=CarbonRecordOut, summary="获取某条碳核算记录")
def get_carbon_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(CarbonRecord)
        .filter(CarbonRecord.id == record_id, CarbonRecord.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.delete("/records/{record_id}", summary="删除碳核算记录")
def delete_carbon_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(CarbonRecord)
        .filter(CarbonRecord.id == record_id, CarbonRecord.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"success": True, "message": "记录已删除"}
