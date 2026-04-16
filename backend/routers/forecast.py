"""预测与预警路由：时序预测 + Conformal 区间。"""
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.carbon import CarbonRecord
from services.forecasting import forecast_service
from utils.auth import get_current_user_optional


router = APIRouter(prefix="/api/forecast", tags=["时序预测与预警"])


class ForecastRequest(BaseModel):
    months_ahead: int = Field(6, ge=1, le=18, description="预测未来月数")
    alpha: float = Field(0.1, ge=0.01, le=0.3, description="Conformal 置信参数")
    use_demo_if_empty: bool = Field(True, description="无历史记录时使用内置演示序列")


class MonthlyPoint(BaseModel):
    month: str
    value: float


def _aggregate_monthly(records: List[CarbonRecord]) -> Dict[str, float]:
    monthly = defaultdict(float)
    for r in records:
        created = r.created_at
        if created is None:
            continue
        month_key = created.strftime("%Y-%m")
        monthly[month_key] += float(r.total_emission or 0.0)
    return dict(monthly)


def _demo_series() -> Dict[str, float]:
    return {
        "2025-07": 9.8,
        "2025-08": 10.6,
        "2025-09": 11.2,
        "2025-10": 10.9,
        "2025-11": 11.8,
        "2025-12": 12.1,
        "2026-01": 12.7,
        "2026-02": 12.3,
        "2026-03": 12.9,
        "2026-04": 13.5,
    }


@router.post("/monthly-carbon", summary="月度碳排趋势预测与预警")
def forecast_monthly_carbon(
    body: ForecastRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    query = db.query(CarbonRecord)
    if current_user is not None:
        query = query.filter(CarbonRecord.user_id == current_user.id)

    records = query.order_by(CarbonRecord.created_at.asc()).all()
    monthly = _aggregate_monthly(records)

    if not monthly and body.use_demo_if_empty:
        monthly = _demo_series()

    result = forecast_service.forecast(
        monthly_series=monthly,
        months_ahead=body.months_ahead,
        alpha=body.alpha,
    )

    return {
        "success": True,
        "history_count": len(result.get("history", [])),
        "forecast_count": len(result.get("forecast", [])),
        **result,
    }
