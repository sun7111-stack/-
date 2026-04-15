"""碳排放核算路由"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.carbon import EmissionFactor, IndustryBenchmark, CarbonRecord
from models.analysis import AnalysisResult, AnalysisBreakdown
from models.analysis_v2 import AnalysisResultV2Snapshot
from models.factor_match_log import FactorMatchLog
from schemas.carbon import (
    EmissionFactorOut,
    IndustryBenchmarkOut,
    CarbonRecordCreate,
    CarbonRecordOut,
    CarbonCalcResult,
    OCRCarbonCalcRequest,
    DynamicCarbonCalcResult,
    CarbonResultV2Out,
    CarbonFlowOut,
    CarbonExplainOut,
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

    records_for_engine = []
    for act, val in activity_data.items():
        records_for_engine.append(
            {
                "activity_id": None,
                "activity_type": act,
                "amount": float(val or 0.0),
                "unit": "",
                "region": body.region,
                "period": body.period,
                "method": "default",
                "dq_activity_level": "C",
            }
        )

    # 4. 按版本执行核算（v1保留，v2默认）
    result = engine.run_calculation(
        records=records_for_engine,
        enterprise_profile={
            "shop_type": body.shop_type,
            "region": body.region,
            "annual_revenue": body.annual_revenue,
            "year": None,
            "method": "default",
        },
        model_version=body.model_version,
        uncertainty_mode=body.uncertainty_mode,
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

    # 5.1 保存规范化分析结果与分项结果
    company_name = (current_user.company or "Demo企业") if current_user else "Demo企业"
    major_source = ""
    if result.get("breakdown"):
        major_source = max(result["breakdown"], key=lambda x: x.get("emission", 0)).get("item", "")
    analysis = AnalysisResult(
        user_id=current_user.id,
        enterprise_name=company_name,
        total_emission=result["total_emission"],
        carbon_intensity=result["benchmark_compare"].get("carbon_intensity", 0.0),
        industry_deviation=result["benchmark_compare"].get("deviation_ratio", 0.0),
        scope1=float((result.get("scope_breakdown") or {}).get("S1", 0.0) or 0.0),
        scope2=float((result.get("scope_breakdown") or {}).get("S2", 0.0) or 0.0),
        scope3=float((result.get("scope_breakdown") or {}).get("S3", 0.0) or 0.0),
        ci95_low=float((result.get("uncertainty") or {}).get("ci95_low", 0.0) or 0.0),
        ci95_high=float((result.get("uncertainty") or {}).get("ci95_high", 0.0) or 0.0),
        uncertainty_mode=body.uncertainty_mode,
        risk_level="medium",
        major_source=major_source,
        top_contributor_activity_id=(result.get("top_contributors") or [{}])[0].get("activity_id") if result.get("top_contributors") else None,
        advice_text="建议优先优化高排放来源并按月复盘。",
    )
    db.add(analysis)
    db.flush()

    # 5.2 保存V2结果快照（用于 /result /flow /explain）
    if (result.get("model_version") or "v1") == "v2":
        snapshot = AnalysisResultV2Snapshot(
            analysis_id=analysis.id,
            model_version="v2",
            uncertainty_mode=body.uncertainty_mode,
            scope_breakdown=result.get("scope_breakdown", {}),
            source_breakdown=result.get("breakdown", []),
            uncertainty=result.get("uncertainty", {}),
            top_contributors=result.get("top_contributors", []),
            factor_trace=result.get("factor_trace", []),
            carbon_flow_graph=result.get("carbon_flow", {}),
            explain_trace=result.get("explain_trace", {}),
        )
        db.add(snapshot)

        for trace in result.get("factor_trace", []):
            matched = trace.get("matched_factor", {})
            db.add(
                FactorMatchLog(
                    analysis_id=analysis.id,
                    activity_id=trace.get("activity_id"),
                    factor_id=matched.get("factor_id"),
                    match_rule="activity+region+year+method",
                    fallback_level=matched.get("fallback_level", ""),
                    match_explain=trace.get("match_reason", ""),
                    factor_value_snapshot=float(matched.get("value", 0.0) or 0.0),
                    factor_source_snapshot=str(matched.get("source", "")),
                )
            )

    total = result["total_emission"] if result["total_emission"] > 0 else 1.0
    for item in result.get("breakdown", []):
        db.add(
            AnalysisBreakdown(
                analysis_id=analysis.id,
                source_type=item.get("item", ""),
                emission_value=float(item.get("emission", 0.0)),
                proportion=round(float(item.get("emission", 0.0)) / total * 100, 2),
            )
        )
    db.commit()

    # 6. 返回格式化结果
    return DynamicCarbonCalcResult(
        record_id=record.id,
        analysis_id=analysis.id,
        total_emission=result["total_emission"],
        breakdown=result["breakdown"],
        benchmark_compare=result["benchmark_compare"],
        carbon_flow=result.get("carbon_flow"),
        scope_breakdown=result.get("scope_breakdown"),
        uncertainty=result.get("uncertainty"),
        top_contributors=result.get("top_contributors"),
        factor_trace=result.get("factor_trace"),
        model_version=result.get("model_version", "v1"),
        message="智能碳核算与场景拆解完成"
    )


@router.get("/result/{analysis_id}", response_model=CarbonResultV2Out, summary="获取碳核算V2结果")
def get_carbon_result_v2(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.id == analysis_id, AnalysisResult.user_id == current_user.id)
        .first()
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="analysis不存在")

    snapshot = (
        db.query(AnalysisResultV2Snapshot)
        .filter(AnalysisResultV2Snapshot.analysis_id == analysis_id)
        .first()
    )
    if snapshot is None:
        raise HTTPException(status_code=404, detail="该分析尚无v2快照")

    return CarbonResultV2Out(
        analysis_id=analysis_id,
        model_version=snapshot.model_version,
        total_emission=analysis.total_emission,
        breakdown=snapshot.source_breakdown,
        scope_breakdown=snapshot.scope_breakdown,
        benchmark_compare={
            "industry_deviation": analysis.industry_deviation,
            "carbon_intensity": analysis.carbon_intensity,
            "risk_level": analysis.risk_level,
        },
        uncertainty=snapshot.uncertainty,
        top_contributors=snapshot.top_contributors,
        factor_trace=snapshot.factor_trace,
    )


@router.get("/flow/{analysis_id}", response_model=CarbonFlowOut, summary="获取碳流Sankey数据")
def get_carbon_flow_v2(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.id == analysis_id, AnalysisResult.user_id == current_user.id)
        .first()
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="analysis不存在")

    snapshot = (
        db.query(AnalysisResultV2Snapshot)
        .filter(AnalysisResultV2Snapshot.analysis_id == analysis_id)
        .first()
    )
    if snapshot is None:
        raise HTTPException(status_code=404, detail="该分析尚无v2快照")

    return CarbonFlowOut(analysis_id=analysis_id, carbon_flow=snapshot.carbon_flow_graph)


@router.get("/explain/{analysis_id}", response_model=CarbonExplainOut, summary="获取可解释核算链路")
def get_carbon_explain_v2(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.id == analysis_id, AnalysisResult.user_id == current_user.id)
        .first()
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="analysis不存在")

    snapshot = (
        db.query(AnalysisResultV2Snapshot)
        .filter(AnalysisResultV2Snapshot.analysis_id == analysis_id)
        .first()
    )
    if snapshot is None:
        raise HTTPException(status_code=404, detail="该分析尚无v2快照")

    return CarbonExplainOut(analysis_id=analysis_id, explain_trace=snapshot.explain_trace)


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
