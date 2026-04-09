"""ESG评分路由"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.esg import EsgScore
from models.carbon import EmissionFactor, IndustryBenchmark
from models.enterprise import EnterpriseProfile
from schemas.esg import (
    EsgEnvironmentInput,
    EsgSocialInput,
    EsgGovernanceInput,
    EsgFullInput,
    EsgScoreOut,
    EsgDimensionResult,
    EsgTotalResult,
)
from utils.auth import get_current_user
from utils.calculator import (
    calculate_env_score,
    calculate_social_score,
    calculate_governance_score,
    generate_recommendations,
)

router = APIRouter(prefix="/api/esg", tags=["ESG评分"])


def _get_factors_and_benchmarks(db: Session):
    """内部: 从DB获取因子和基准"""
    factors_rows = db.query(EmissionFactor).all()
    factors_dict = {f.name: f.factor for f in factors_rows}
    if not factors_dict:
        factors_dict = {"electricity": 0.581, "natural_gas": 1.89, "diesel": 2.68}

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
    return factors_dict, benchmarks_dict


# ========== 单维度计算（不保存进数据库，即时返回） ==========

@router.post("/calculate/environment", response_model=EsgDimensionResult, summary="计算环境(E)维度得分")
def calc_environment(
    body: EsgEnvironmentInput,
    db: Session = Depends(get_db),
):
    factors_dict, benchmarks_dict = _get_factors_and_benchmarks(db)
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
    return EsgDimensionResult(
        score=result["score"],
        level=result["level"],
        message=result["message"],
        details={
            "total_emission": result["total_emission"],
            "carbon_intensity": result["carbon_intensity"],
            "industry_benchmark": result["industry_benchmark"],
            "recycling_rate": result["recycling_rate"],
        },
    )


@router.post("/calculate/social", response_model=EsgDimensionResult, summary="计算社会(S)维度得分")
def calc_social(body: EsgSocialInput):
    result = calculate_social_score(
        employee_scale=body.employee_scale,
        employee_satisfaction=body.employee_satisfaction,
        training_hours=body.training_hours,
        turnover_rate=body.turnover_rate,
        community_investment=body.community_investment,
        supplier_esg=body.supplier_esg,
        customer_satisfaction=body.customer_satisfaction,
        complaint_rate=body.complaint_rate,
    )
    return EsgDimensionResult(
        score=result["score"],
        level=result["level"],
        message=result["message"],
        details={
            "employee_satisfaction": body.employee_satisfaction,
            "training_hours": body.training_hours,
            "turnover_rate": body.turnover_rate,
            "customer_satisfaction": body.customer_satisfaction,
        },
    )


@router.post("/calculate/governance", response_model=EsgDimensionResult, summary="计算治理(G)维度得分")
def calc_governance(body: EsgGovernanceInput):
    result = calculate_governance_score(
        ownership_type=body.ownership_type,
        governance_level=body.governance_level,
        independent_directors=body.independent_directors,
        female_directors=body.female_directors,
        compliance_training=body.compliance_training,
        anti_corruption=body.anti_corruption,
        esg_disclosure=body.esg_disclosure,
        audit_independence=body.audit_independence,
        risk_management=body.risk_management,
        data_security=body.data_security,
    )
    return EsgDimensionResult(
        score=result["score"],
        level=result["level"],
        message=result["message"],
        details={
            "independent_directors": body.independent_directors,
            "female_directors": body.female_directors,
            "esg_disclosure": body.esg_disclosure,
            "risk_management": body.risk_management,
        },
    )


# ========== 综合评估（计算三维度并保存） ==========

@router.post("/calculate/total", response_model=EsgTotalResult, summary="综合ESG评估并保存")
def calc_total(
    body: EsgFullInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    factors_dict, benchmarks_dict = _get_factors_and_benchmarks(db)

    env_result = calculate_env_score(
        company_type=body.environment.company_type,
        annual_revenue=body.environment.annual_revenue,
        electricity_usage=body.environment.electricity_usage,
        gas_usage=body.environment.gas_usage,
        fuel_usage=body.environment.fuel_usage,
        waste_generation=body.environment.waste_generation,
        recycling_rate=body.environment.recycling_rate,
        emission_factors=factors_dict,
        industry_benchmarks=benchmarks_dict,
    )
    soc_result = calculate_social_score(
        employee_scale=body.social.employee_scale,
        employee_satisfaction=body.social.employee_satisfaction,
        training_hours=body.social.training_hours,
        turnover_rate=body.social.turnover_rate,
        community_investment=body.social.community_investment,
        supplier_esg=body.social.supplier_esg,
        customer_satisfaction=body.social.customer_satisfaction,
        complaint_rate=body.social.complaint_rate,
    )
    gov_result = calculate_governance_score(
        ownership_type=body.governance.ownership_type,
        governance_level=body.governance.governance_level,
        independent_directors=body.governance.independent_directors,
        female_directors=body.governance.female_directors,
        compliance_training=body.governance.compliance_training,
        anti_corruption=body.governance.anti_corruption,
        esg_disclosure=body.governance.esg_disclosure,
        audit_independence=body.governance.audit_independence,
        risk_management=body.governance.risk_management,
        data_security=body.governance.data_security,
    )

    e, s, g = env_result["score"], soc_result["score"], gov_result["score"]
    total = round(e * 0.4 + s * 0.3 + g * 0.3)
    recs = generate_recommendations(e, s, g)

    if total >= 80:
        level = "优秀"
    elif total >= 60:
        level = "良好"
    else:
        level = "待改进"

    # 保存到数据库
    record = EsgScore(
        user_id=current_user.id,
        environment=e,
        social=s,
        governance=g,
        total=total,
        env_electricity_usage=body.environment.electricity_usage,
        env_gas_usage=body.environment.gas_usage,
        env_fuel_usage=body.environment.fuel_usage,
        env_waste_generation=body.environment.waste_generation,
        env_recycling_rate=body.environment.recycling_rate,
        soc_employee_satisfaction=body.social.employee_satisfaction,
        soc_training_hours=body.social.training_hours,
        soc_turnover_rate=body.social.turnover_rate,
        soc_community_investment=body.social.community_investment,
        soc_supplier_esg=body.social.supplier_esg,
        soc_customer_satisfaction=body.social.customer_satisfaction,
        soc_complaint_rate=body.social.complaint_rate,
        gov_governance_level=body.governance.governance_level,
        gov_independent_directors=body.governance.independent_directors,
        gov_female_directors=body.governance.female_directors,
        gov_compliance_training=body.governance.compliance_training,
        gov_anti_corruption=body.governance.anti_corruption,
        gov_esg_disclosure=body.governance.esg_disclosure,
        gov_audit_independence=body.governance.audit_independence,
        gov_risk_management=body.governance.risk_management,
        gov_data_security=body.governance.data_security,
        recommendations=recs,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return EsgTotalResult(
        record_id=record.id,
        environment=e,
        social=s,
        governance=g,
        total=total,
        level=level,
        recommendations=recs,
    )


# ========== 查询ESG历史 ==========

@router.get("/history", response_model=List[EsgScoreOut], summary="获取ESG评分历史")
def get_esg_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(EsgScore)
        .filter(EsgScore.user_id == current_user.id)
        .order_by(EsgScore.created_at.desc())
        .limit(50)
        .all()
    )
    return records


@router.get("/history/{record_id}", response_model=EsgScoreOut, summary="获取ESG评分详情")
def get_esg_detail(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(EsgScore)
        .filter(EsgScore.id == record_id, EsgScore.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


# ============================================================
# 评分详情（对应截图：ESG评分·电商商家，含维度/行业均值/细分指标）
# ============================================================

# 行业平均分基准（用于对标）
INDUSTRY_AVERAGES = {
    "ecommerce":   {"E": 72, "S": 82, "G": 85},
    "manufacture":  {"E": 68, "S": 75, "G": 78},
    "logistics":    {"E": 65, "S": 78, "G": 80},
    "service":      {"E": 74, "S": 84, "G": 86},
    "default":      {"E": 70, "S": 80, "G": 82},
}

# 行业中文名映射
INDUSTRY_CN = {
    "ecommerce": "电商商家",
    "manufacture": "制造企业",
    "logistics": "物流企业",
    "service": "服务企业",
    "金属制品": "制造企业",
    "电子商务": "电商商家",
}


@router.get("/score-detail", summary="ESG评分详情（含维度、行业均值、细分指标）")
def get_score_detail(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    返回截图所示的完整ESG评分详情:
    - 综合得分 + 等级
    - E/S/G 三维度: 得分、权重、行业平均
    - 细分指标（百分比进度条）
    - 改进建议
    """
    # 获取最新ESG记录
    latest = (
        db.query(EsgScore)
        .filter(EsgScore.user_id == current_user.id)
        .order_by(EsgScore.created_at.desc())
        .first()
    )

    # 获取企业档案
    profile = db.query(EnterpriseProfile).filter(
        EnterpriseProfile.user_id == current_user.id
    ).first()

    industry_key = "default"
    industry_label = "(示例)"
    if profile:
        industry_label = INDUSTRY_CN.get(profile.industry, profile.industry or "(示例)")
        for k, v in INDUSTRY_CN.items():
            if v == industry_label:
                if k in INDUSTRY_AVERAGES:
                    industry_key = k
                    break
        if industry_key == "default" and profile.industry in INDUSTRY_AVERAGES:
            industry_key = profile.industry

    if latest:
        e, s, g, total = latest.environment, latest.social, latest.governance, latest.total
    elif profile and profile.esg_score:
        total = profile.esg_score
        e, s, g = 79, 88, 91
    else:
        e, s, g, total = 79, 88, 91, 86

    level = "优秀" if total >= 80 else ("良好" if total >= 60 else "待改进")
    avg = INDUSTRY_AVERAGES.get(industry_key, INDUSTRY_AVERAGES["default"])

    # 细分指标（根据行业生成）
    sub_indicators = _generate_sub_indicators(industry_key, e, s, g)
    # 改进建议
    suggestions = _generate_suggestions(industry_key, e, s, g, sub_indicators)

    return {
        "title": f"ESG评分 · {industry_label}",
        "total_score": total,
        "level": level,
        "dimensions": [
            {"name": "环境(E)", "score": e, "weight": "40%", "industry_avg": avg["E"]},
            {"name": "社会(S)", "score": s, "weight": "35%", "industry_avg": avg["S"]},
            {"name": "治理(G)", "score": g, "weight": "25%", "industry_avg": avg["G"]},
        ],
        "sub_indicators": sub_indicators,
        "suggestions": suggestions,
        "radar_data": {"labels": ["环境(E)", "社会(S)", "治理(G)"], "values": [e, s, g]},
    }


# ============================================================
# 对标分析
# ============================================================

@router.get("/benchmark", summary="对标分析")
def get_benchmark(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    latest = (
        db.query(EsgScore)
        .filter(EsgScore.user_id == current_user.id)
        .order_by(EsgScore.created_at.desc())
        .first()
    )
    profile = db.query(EnterpriseProfile).filter(
        EnterpriseProfile.user_id == current_user.id
    ).first()

    if latest:
        e, s, g, total = latest.environment, latest.social, latest.governance, latest.total
    elif profile:
        total = profile.esg_score or 72
        e, s, g = 79, 88, 91
    else:
        e, s, g, total = 79, 88, 91, 86

    industry_key = "default"
    if profile:
        for k, v in INDUSTRY_CN.items():
            if profile.industry and (profile.industry in k or k in profile.industry):
                if k in INDUSTRY_AVERAGES:
                    industry_key = k
                    break

    avg = INDUSTRY_AVERAGES.get(industry_key, INDUSTRY_AVERAGES["default"])

    return {
        "my_scores": {"E": e, "S": s, "G": g, "total": total},
        "industry_avg": {"E": avg["E"], "S": avg["S"], "G": avg["G"], "total": round(avg["E"]*0.4 + avg["S"]*0.35 + avg["G"]*0.25)},
        "industry_best": {"E": 95, "S": 96, "G": 97, "total": 96},
        "percentile": 58 if total >= 80 else (35 if total >= 60 else 15),
        "ranking_label": f"优于同行业{58 if total >= 80 else 35}%企业",
        "gaps": [
            {"dimension": "环境(E)", "gap": avg["E"] - e if e < avg["E"] else 0, "suggestion": "提升清洁能源使用比例"},
            {"dimension": "社会(S)", "gap": avg["S"] - s if s < avg["S"] else 0, "suggestion": "加强员工培训与福利"},
            {"dimension": "治理(G)", "gap": avg["G"] - g if g < avg["G"] else 0, "suggestion": "完善ESG信息披露"},
        ],
    }


# ============================================================
# 改进计划
# ============================================================

@router.get("/improvement-plans", summary="改进计划")
def get_improvement_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    latest = (
        db.query(EsgScore)
        .filter(EsgScore.user_id == current_user.id)
        .order_by(EsgScore.created_at.desc())
        .first()
    )
    e = latest.environment if latest else 79

    plans = [
        {
            "id": 1,
            "dimension": "环境(E)",
            "title": "提升新能源物流车比例",
            "description": "当前新能源物流车比例仅20%，目标提升至50%",
            "priority": "high",
            "status": "进行中",
            "target_score_increase": 5,
            "deadline": "2026-06-30",
            "progress": 35,
        },
        {
            "id": 2,
            "dimension": "环境(E)",
            "title": "包装材料绿色化改造",
            "description": "推广可降解包装，减少塑料使用量",
            "priority": "medium",
            "status": "计划中",
            "target_score_increase": 3,
            "deadline": "2026-09-30",
            "progress": 10,
        },
        {
            "id": 3,
            "dimension": "社会(S)",
            "title": "员工ESG培训体系",
            "description": "建立ESG相关的员工培训计划，每年不少于20学时",
            "priority": "medium",
            "status": "进行中",
            "target_score_increase": 2,
            "deadline": "2026-12-31",
            "progress": 50,
        },
        {
            "id": 4,
            "dimension": "治理(G)",
            "title": "ESG信息披露完善",
            "description": "按照GRI标准完善ESG年度报告披露",
            "priority": "low",
            "status": "计划中",
            "target_score_increase": 4,
            "deadline": "2026-12-31",
            "progress": 0,
        },
    ]
    return {"plans": plans, "total_target_increase": sum(p["target_score_increase"] for p in plans)}


# ============================================================
# 历史趋势
# ============================================================

@router.get("/trends", summary="ESG历史趋势数据")
def get_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(EsgScore)
        .filter(EsgScore.user_id == current_user.id)
        .order_by(EsgScore.created_at.asc())
        .limit(12)
        .all()
    )

    if records:
        data = [
            {
                "date": r.created_at.strftime("%Y-%m") if r.created_at else f"记录{i+1}",
                "E": r.environment,
                "S": r.social,
                "G": r.governance,
                "total": r.total,
            }
            for i, r in enumerate(records)
        ]
    else:
        # 模拟历史趋势
        data = [
            {"date": "2025-Q1", "E": 72, "S": 80, "G": 85, "total": 78},
            {"date": "2025-Q2", "E": 74, "S": 83, "G": 87, "total": 80},
            {"date": "2025-Q3", "E": 76, "S": 85, "G": 89, "total": 82},
            {"date": "2025-Q4", "E": 79, "S": 88, "G": 91, "total": 86},
        ]

    return {
        "trend_data": data,
        "summary": {
            "total_improvement": data[-1]["total"] - data[0]["total"] if len(data) >= 2 else 0,
            "best_dimension": "治理(G)",
            "weakest_dimension": "环境(E)",
        },
    }


# ============================================================
# 辅助函数
# ============================================================

def _generate_sub_indicators(industry_key: str, e: float, s: float, g: float) -> list:
    """根据行业和得分生成细分指标"""
    if industry_key in ("ecommerce", "default"):
        return [
            {"name": "包装减碳", "value": 68, "color": "#2d6a4f"},
            {"name": "物流绿色化", "value": 55, "color": "#95d5b2"},
            {"name": "消费者权益", "value": 92, "color": "#40916c"},
        ]
    elif industry_key == "manufacture":
        return [
            {"name": "清洁生产", "value": 72, "color": "#2d6a4f"},
            {"name": "废弃物管理", "value": 65, "color": "#95d5b2"},
            {"name": "安全生产", "value": 88, "color": "#40916c"},
        ]
    elif industry_key == "logistics":
        return [
            {"name": "运输碳效", "value": 60, "color": "#2d6a4f"},
            {"name": "仓储节能", "value": 70, "color": "#95d5b2"},
            {"name": "包装回收", "value": 78, "color": "#40916c"},
        ]
    else:
        return [
            {"name": "能源效率", "value": int(e * 0.85), "color": "#2d6a4f"},
            {"name": "社区贡献", "value": int(s * 0.9), "color": "#95d5b2"},
            {"name": "信息透明", "value": int(g * 0.95), "color": "#40916c"},
        ]


def _generate_suggestions(industry_key: str, e: float, s: float, g: float, sub_indicators: list) -> list:
    """根据维度得分和细分指标生成改进建议"""
    suggestions = []
    weakest = min(sub_indicators, key=lambda x: x["value"])
    suggestions.append(f"重点关注「{weakest['name']}」指标，当前仅{weakest['value']}%")

    if e < 80:
        suggestions.append("提升新能源物流车比例，目前仅20%")
    if s < 85:
        suggestions.append("建议增强供应商ESG管理覆盖面")
    if g < 88:
        suggestions.append("完善ESG治理架构与信息披露机制")

    return suggestions
