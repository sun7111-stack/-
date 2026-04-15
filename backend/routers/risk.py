"""风险检测路由：Isolation Forest + 数据确权"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.carbon import CarbonRecord
from models.analysis import AnalysisResult, RiskResult
from models.flow import TrustScoreRecord
from services.risk_detector import (
    RiskInputData,
    risk_detector,
    calculate_risk_score,
    calculate_risk_score_v2,
    classify_risk_level,
    generate_risk_reasons,
    generate_risk_advice,
)
from services.security import generate_data_hash, save_data_trace
from utils.auth import get_current_user_optional

router = APIRouter(prefix="/api/risk", tags=["风控检测"])


class RiskDetectRequest(BaseModel):
    task_id: Optional[str] = None
    bill_id: Optional[str] = None
    raw_text: Optional[str] = ""
    structured_fields: Optional[dict] = None

    electricity_usage: Optional[float] = None
    logistics_distance: Optional[float] = None
    return_rate: Optional[float] = None
    total_emission: Optional[float] = None
    carbon_intensity: Optional[float] = None


def _build_input_from_request(body: RiskDetectRequest, latest: Optional[CarbonRecord]) -> RiskInputData:
    electricity_usage = body.electricity_usage
    total_emission = body.total_emission
    carbon_intensity = body.carbon_intensity

    if latest is not None:
        if electricity_usage is None:
            electricity_usage = latest.electricity_usage
        if total_emission is None:
            total_emission = latest.total_emission / 1000 if latest.total_emission > 100 else latest.total_emission
        if carbon_intensity is None:
            carbon_intensity = latest.carbon_intensity

    return RiskInputData(
        electricity_usage=electricity_usage or 5000,
        logistics_distance=body.logistics_distance or 10000,
        return_rate=body.return_rate or 0.08,
        total_emission=total_emission or 50,
        carbon_intensity=carbon_intensity or 0.6,
    )


@router.post("/detect", summary="Isolation Forest风控检测")
def detect_risk(
    body: RiskDetectRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    try:
        latest = None
        if current_user is not None:
            try:
                latest = (
                    db.query(CarbonRecord)
                    .filter(CarbonRecord.user_id == current_user.id)
                    .order_by(CarbonRecord.created_at.desc())
                    .first()
                )
            except Exception:
                # DB 不可用时继续执行风控，保证演示链路可用
                latest = None

        detector_input = _build_input_from_request(body, latest)
        risk_result = risk_detector.detect(detector_input)

        # Rc: 模型异常风险, Re: ESG风险(缺省按75分映射), Rg: 治理/信用风险
        carbon_risk = float(risk_result.risk_score)
        esg_score = 75.0
        if body.structured_fields and isinstance(body.structured_fields, dict):
            esg_score = float(body.structured_fields.get("esg_score", 75.0) or 75.0)
        esg_risk = max(0.0, min(100.0, 100.0 - esg_score))
        governance_risk = max(0.0, min(100.0, detector_input.return_rate * 100 + detector_input.carbon_intensity * 20))

        trust_score = 0.6
        latest_analysis_for_trust = None
        if current_user is not None:
            latest_analysis_for_trust = (
                db.query(AnalysisResult)
                .filter(AnalysisResult.user_id == current_user.id)
                .order_by(AnalysisResult.analysis_time.desc())
                .first()
            )
        if latest_analysis_for_trust is not None:
            trust_row = (
                db.query(TrustScoreRecord)
                .filter(TrustScoreRecord.analysis_id == str(latest_analysis_for_trust.id))
                .first()
            )
            if trust_row is not None:
                trust_score = max(0.0, min(1.0, float(trust_row.trust_score) / 100.0))

        anomaly_risk = float(risk_result.risk_score)

        explain_score = calculate_risk_score(
            carbon_risk=carbon_risk,
            esg_risk=esg_risk,
            governance_risk=governance_risk,
        )
        explain_score_v2 = calculate_risk_score_v2(
            carbon_risk=carbon_risk,
            esg_risk=esg_risk,
            governance_risk=governance_risk,
            trust_score=trust_score,
            anomaly_risk=anomaly_risk,
        )
        risk_level = classify_risk_level(explain_score_v2)
        # 统一口径：出现异常样本时，等级不低于中风险，避免 "is_anomaly=True 但 low" 的歧义。
        if risk_result.is_anomaly and risk_level == "low":
            risk_level = "medium"
        risk_reasons = generate_risk_reasons(
            carbon_risk=carbon_risk,
            esg_risk=esg_risk,
            governance_risk=governance_risk,
            anomaly_labels=risk_result.anomaly_labels,
        )
        risk_advice = generate_risk_advice(risk_level=risk_level, reasons=risk_reasons)

        trace_payload = body.structured_fields or detector_input.model_dump()
        user_id = current_user.id if current_user is not None else 0
        raw_text = body.raw_text or "risk-detect-payload"
        bill_id = body.bill_id or body.task_id or f"risk-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        trace_saved = True
        try:
            latest_analysis = None
            if current_user is not None:
                latest_analysis = (
                    db.query(AnalysisResult)
                    .filter(AnalysisResult.user_id == current_user.id)
                    .order_by(AnalysisResult.analysis_time.desc())
                    .first()
                )

            if current_user is not None:
                db.add(
                    RiskResult(
                        user_id=current_user.id,
                        analysis_id=latest_analysis.id if latest_analysis else None,
                        risk_score=explain_score_v2,
                        risk_level=risk_level,
                        risk_reason="；".join(risk_reasons),
                        risk_advice="；".join(risk_advice),
                    )
                )
                db.commit()

            trace_record = save_data_trace(
                db=db,
                raw_text=raw_text,
                structured_fields=trace_payload,
                user_id=user_id,
                bill_id=bill_id,
                doc_type="risk_input",
            )
            blockchain_hash = trace_record.data_hash
        except Exception:
            blockchain_hash, _ = generate_data_hash(raw_text, trace_payload, user_id)
            trace_saved = False

        return {
            "success": True,
            "task_id": body.task_id or f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "is_anomaly": risk_result.is_anomaly,
            "risk_score": risk_result.risk_score,
            "risk_score_explain": explain_score,
            "risk_score_explain_v2": explain_score_v2,
            "risk_level": risk_level,
            "trust_score": round(trust_score, 4),
            "trust_penalty": round((1.0 - trust_score) * 100.0, 2),
            "risk_reasons": risk_reasons,
            "risk_advice": risk_advice,
            "anomaly_labels": risk_result.anomaly_labels,
            "details": risk_result.anomaly_labels,
            "blockchain_hash": blockchain_hash,
            "trace_saved": trace_saved,
            "model_version": risk_result.model_version,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"风控检测失败: {str(e)}")
