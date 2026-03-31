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
    OCRCarbonCalcRequest,
    DynamicCarbonCalcResult,
)
from utils.auth import get_current_user
from utils.calculator import calculate_env_score
from services.carbon_engine.engine import CarbonEngine

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


@router.post("/calculate", response_model=DynamicCarbonCalcResult, summary="执行基于策略模式的碳核算")
def calculate_carbon(
    body: OCRCarbonCalcRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. 提取或初始化活动数据
    activity_data = body.activity_data.copy() if hasattr(body, "activity_data") and body.activity_data else {}

    # 2. 将 OCR/VLM 的结构化字段映射成核算用数据
    if body.fields and body.suggested_activity_type:
        act_type = body.suggested_activity_type
        amount = 0.0
        # 简单启发式搜索：寻找票据/表单里的主要额度/用量
        for k, v in body.fields.items():
            if isinstance(v, (int, float)):
                amount = float(v)
                break
            elif isinstance(v, str) and v.replace('.', '', 1).isdigit():
                amount = float(v)
                break
        
        # 将本次 OCR 提取的量合并入引擎输入
        if amount > 0:
            if act_type not in activity_data:
                activity_data[act_type] = amount
            else:
                activity_data[act_type] += amount

    # 3. 初始化并调用策略引擎
    engine = CarbonEngine(db_session=db)
    
    # 4. 识别店铺/行业类型并执行差异化计算 (包含总碳排、分解与同业对比)
    result = engine.run_calculation(
        activity_data=activity_data,
        shop_type=body.shop_type,
        region=body.region,
        revenue=body.annual_revenue
    )

    # 5. 落库持久化（原有的模型可以考虑重构或精简，这里直接存基本信息和总量）
    record = CarbonRecord(
        user_id=current_user.id,
        company_type=body.shop_type,
        annual_revenue=body.annual_revenue,
        electricity_usage=activity_data.get("electricity", 0.0),
        gas_usage=activity_data.get("natural_gas", 0.0),
        fuel_usage=activity_data.get("diesel", 0.0),
        waste_generation=activity_data.get("waste", 0.0),
        total_emission=result["total_emission"],
        carbon_intensity=result["benchmark_compare"].get("carbon_intensity", 0.0),
        period=body.period,
        note=f"基于策略模式核算引擎 | 店铺类型: {body.shop_type} | OCR来源: {body.doc_type}",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # 6. 返回格式化结果
    return DynamicCarbonCalcResult(
        record_id=record.id,
        total_emission=result["total_emission"],
        breakdown=result["breakdown"],
        benchmark_compare=result["benchmark_compare"],
        message="智能碳核算与场景拆解完成"
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
