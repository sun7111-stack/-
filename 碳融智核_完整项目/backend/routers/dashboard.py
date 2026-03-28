"""数据驾驶舱路由 - 碳排放监控 / 能耗结构 / ESG看板 / 关键指标"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.carbon import CarbonRecord
from models.esg import EsgScore
from models.enterprise import EnterpriseProfile
from schemas.dashboard import (
    EmissionMonitor,
    EmissionPoint,
    EnergyStructure,
    EnergyStructureItem,
    EsgBoard,
    EsgBoardItem,
    KeyIndicators,
    KeyIndicator,
)
from utils.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["数据驾驶舱"])


# ============================================================
# 碳排放监控
# ============================================================

@router.get("/emission-monitor", response_model=EmissionMonitor, summary="碳排放监控(月度折线)")
def emission_monitor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """返回月度碳排放数据，用于前端折线图"""
    records = (
        db.query(CarbonRecord)
        .filter(CarbonRecord.user_id == current_user.id)
        .order_by(CarbonRecord.created_at.desc())
        .limit(12)
        .all()
    )

    # 从企业档案获取总排放
    profile = db.query(EnterpriseProfile).filter(
        EnterpriseProfile.user_id == current_user.id
    ).first()
    base_emission = profile.total_carbon_emission if profile else 500

    # 生成月度数据（模拟逐月下降趋势）
    if records and len(records) >= 4:
        data = []
        for i, r in enumerate(reversed(records[:12])):
            data.append(EmissionPoint(
                month=f"{i+1}月",
                emission=round(r.total_emission / 1000, 1)  # kg -> t
            ))
    else:
        # 使用企业数据生成模拟月度趋势
        quarterly = base_emission / 4
        monthly_base = quarterly / 3
        data = [
            EmissionPoint(month="1月", emission=round(monthly_base * 1.10, 1)),
            EmissionPoint(month="2月", emission=round(monthly_base * 1.07, 1)),
            EmissionPoint(month="3月", emission=round(monthly_base * 1.00, 1)),
            EmissionPoint(month="4月", emission=round(monthly_base * 0.95, 1)),
        ]

    total = sum(d.emission for d in data)
    return EmissionMonitor(
        title="数据驾驶舱 · emission-monitor",
        unit="t",
        data=data,
        total=round(total, 1),
        yoy_change=-12.6,
        trend="down",
    )


# ============================================================
# 能耗结构
# ============================================================

@router.get("/energy-structure", response_model=EnergyStructure, summary="能耗结构(饼图)")
def energy_structure(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    latest = (
        db.query(CarbonRecord)
        .filter(CarbonRecord.user_id == current_user.id)
        .order_by(CarbonRecord.created_at.desc())
        .first()
    )

    if latest:
        elec = latest.electricity_usage
        gas = latest.gas_usage * 10.5
        fuel = latest.fuel_usage * 9.8
    else:
        elec, gas, fuel = 12450, 8925, 3136

    total = elec + gas + fuel or 1
    items = [
        EnergyStructureItem(
            name="电力", value=round(elec, 1),
            percentage=round(elec / total * 100, 1),
            unit="kWh", color="#2d6a4f"
        ),
        EnergyStructureItem(
            name="天然气", value=round(gas, 1),
            percentage=round(gas / total * 100, 1),
            unit="kWh(eq)", color="#40916c"
        ),
        EnergyStructureItem(
            name="燃油", value=round(fuel, 1),
            percentage=round(fuel / total * 100, 1),
            unit="kWh(eq)", color="#95d5b2"
        ),
    ]

    return EnergyStructure(
        title="能耗结构",
        items=items,
        total_kwh=round(total, 1),
    )


# ============================================================
# ESG看板
# ============================================================

@router.get("/esg-board", response_model=EsgBoard, summary="ESG看板")
def esg_board(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    latest = (
        db.query(EsgScore)
        .filter(EsgScore.user_id == current_user.id)
        .order_by(EsgScore.created_at.desc())
        .first()
    )
    prev = (
        db.query(EsgScore)
        .filter(EsgScore.user_id == current_user.id)
        .order_by(EsgScore.created_at.desc())
        .offset(1).first()
    )

    if latest:
        e, s, g, t = latest.environment, latest.social, latest.governance, latest.total
    else:
        profile = db.query(EnterpriseProfile).filter(
            EnterpriseProfile.user_id == current_user.id
        ).first()
        t = profile.esg_score if profile else 72
        e, s, g = 79, 88, 91

    pe = prev.environment if prev else e - 2
    ps = prev.social if prev else s - 1
    pg = prev.governance if prev else g - 3

    level = "优秀" if t >= 80 else ("良好" if t >= 60 else "待改进")

    return EsgBoard(
        total_score=t,
        level=level,
        dimensions=[
            EsgBoardItem(dimension="环境(E)", score=e, change=round(e - pe, 1), trend="up" if e >= pe else "down"),
            EsgBoardItem(dimension="社会(S)", score=s, change=round(s - ps, 1), trend="up" if s >= ps else "down"),
            EsgBoardItem(dimension="治理(G)", score=g, change=round(g - pg, 1), trend="up" if g >= pg else "down"),
        ],
        industry_rank="前25%",
        percentile=75.0,
    )


# ============================================================
# 关键指标
# ============================================================

@router.get("/key-indicators", response_model=KeyIndicators, summary="关键指标KPI")
def key_indicators(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(EnterpriseProfile).filter(
        EnterpriseProfile.user_id == current_user.id
    ).first()

    if profile:
        emission = profile.total_carbon_emission
        esg = profile.esg_score
        intensity = profile.logistics_carbon_intensity
        energy_int = profile.energy_intensity
        grade = profile.carbon_efficiency_grade
    else:
        emission, esg, intensity, energy_int, grade = 486, 86, 0.13, 0.21, "B+"

    indicators = [
        KeyIndicator(name="碳排放总量", value=str(emission), unit="tCO₂", trend="down", change="-12.6%", icon="cloud"),
        KeyIndicator(name="ESG综合得分", value=str(esg), unit="分", trend="up", change="+3", icon="star"),
        KeyIndicator(name="碳排放强度", value=str(intensity), unit="tCO₂/万元", trend="down", change="-8.3%", icon="chart-line"),
        KeyIndicator(name="能耗强度", value=str(energy_int), unit="tce/万元", trend="down", change="-5.1%", icon="bolt"),
        KeyIndicator(name="碳效等级", value=grade, unit="", trend="up", change="↑1级", icon="award"),
        KeyIndicator(name="绿色收入占比", value="34.2", unit="%", trend="up", change="+6.8%", icon="leaf"),
    ]

    return KeyIndicators(indicators=indicators)
