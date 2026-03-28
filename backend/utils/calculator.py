"""ESG计算引擎 —— 将前端script.js中的计算逻辑搬到后端"""


def calculate_env_score(
    company_type: str,
    annual_revenue: float,
    electricity_usage: float,
    gas_usage: float,
    fuel_usage: float,
    waste_generation: float,
    recycling_rate: float,
    emission_factors: dict,
    industry_benchmarks: dict,
) -> dict:
    """
    计算环境(E)维度得分，逻辑对齐前端 calculateEnvironmental()
    返回: dict(score, total_emission, carbon_intensity, industry_benchmark, level, message)
    """
    factors = emission_factors
    electricity_factor = factors.get("electricity", 0.581)
    gas_factor = factors.get("natural_gas", 1.89)
    fuel_factor = factors.get("diesel", 2.68)

    # 碳排放
    carbon_emission = (
        electricity_usage * electricity_factor
        + gas_usage * gas_factor
        + fuel_usage * fuel_factor
    )

    # 碳强度
    revenue = max(annual_revenue, 1)
    carbon_intensity = carbon_emission / (revenue * 10000)

    # 行业基准
    benchmark = industry_benchmarks.get(company_type, industry_benchmarks.get("manufacture", {}))
    industry_carbon = benchmark.get("carbon_per_revenue", 0.5)

    # 分项计算
    carbon_score = max(0, 100 - (carbon_intensity / max(industry_carbon, 0.001)) * 100)
    energy_per_rev = (electricity_usage + gas_usage * 10 + fuel_usage * 10) / revenue
    energy_benchmark = benchmark.get("energy_metric", 1)
    energy_score = max(0, 100 - (energy_per_rev / max(energy_benchmark, 0.001)) * 50)
    waste_score = recycling_rate
    clean_energy_score = 20 if electricity_usage > 0 else 0

    env_score = (
        carbon_score * 0.4
        + energy_score * 0.3
        + waste_score * 0.2
        + clean_energy_score * 0.1
    )
    env_score = min(100, max(0, round(env_score)))

    if env_score >= 80:
        level, message = "优秀", "优秀水平，远低于行业平均"
    elif env_score >= 60:
        level, message = "良好", "良好水平，接近行业平均"
    else:
        level, message = "待改进", "待改进水平，建议优化能源结构"

    return {
        "score": env_score,
        "total_emission": round(carbon_emission, 2),
        "carbon_intensity": round(carbon_intensity, 6),
        "industry_benchmark": round(industry_carbon, 4),
        "recycling_rate": recycling_rate,
        "level": level,
        "message": message,
    }


def calculate_social_score(
    employee_scale: str,
    employee_satisfaction: float,
    training_hours: float,
    turnover_rate: float,
    community_investment: float,
    supplier_esg: float,
    customer_satisfaction: float,
    complaint_rate: float,
) -> dict:
    """
    计算社会(S)维度得分，逻辑对齐前端 calculateSocial()
    """
    social_score = 0.0

    # 1. 员工满意度(15%)
    social_score += employee_satisfaction * 0.15

    # 2. 培训发展(15%)
    if training_hours >= 40:
        ts = 100
    elif training_hours >= 30:
        ts = 80
    elif training_hours >= 20:
        ts = 60
    elif training_hours >= 10:
        ts = 40
    else:
        ts = 20
    social_score += ts * 0.15

    # 3. 员工流失率(10%)
    if turnover_rate <= 5:
        to = 100
    elif turnover_rate <= 10:
        to = 80
    elif turnover_rate <= 15:
        to = 60
    elif turnover_rate <= 20:
        to = 40
    else:
        to = 20
    social_score += to * 0.10

    # 4. 社区投资(10%)
    if community_investment >= 100:
        cs = 100
    elif community_investment >= 50:
        cs = 80
    elif community_investment >= 20:
        cs = 60
    elif community_investment >= 10:
        cs = 40
    else:
        cs = 20
    social_score += cs * 0.10

    # 5. 供应链责任(10%)
    social_score += supplier_esg * 0.10

    # 6. 客户满意度(25%)
    social_score += customer_satisfaction * 0.25

    # 7. 投诉率(15%)
    if complaint_rate <= 1:
        cps = 100
    elif complaint_rate <= 3:
        cps = 80
    elif complaint_rate <= 5:
        cps = 60
    elif complaint_rate <= 10:
        cps = 40
    else:
        cps = 20
    social_score += cps * 0.15

    # 规模调整
    if employee_scale == "small":
        social_score *= 1.1
    elif employee_scale == "large":
        social_score *= 0.95

    social_score = min(100, max(0, round(social_score)))

    if social_score >= 80:
        level, message = "优秀", "优秀的社会责任表现"
    elif social_score >= 60:
        level, message = "良好", "良好的社会责任基础"
    else:
        level, message = "待改进", "需要加强社会责任建设"

    return {"score": social_score, "level": level, "message": message}


def calculate_governance_score(
    ownership_type: str,
    governance_level: float,
    independent_directors: float,
    female_directors: float,
    compliance_training: float,
    anti_corruption: float,
    esg_disclosure: float,
    audit_independence: float,
    risk_management: float,
    data_security: float,
) -> dict:
    """
    计算治理(G)维度得分，逻辑对齐前端 calculateGovernance()
    """
    gov_score = 0.0

    # 独立董事(10%)
    if independent_directors >= 40:
        ids = 100
    elif independent_directors >= 30:
        ids = 80
    elif independent_directors >= 20:
        ids = 60
    elif independent_directors >= 10:
        ids = 40
    else:
        ids = 20
    gov_score += ids * 0.10

    # 女性董事(10%)
    if female_directors >= 40:
        fds = 100
    elif female_directors >= 30:
        fds = 80
    elif female_directors >= 20:
        fds = 60
    elif female_directors >= 10:
        fds = 40
    else:
        fds = 20
    gov_score += fds * 0.10

    # 治理水平基础分(5%)
    gov_score += governance_level * 0.05

    # 合规培训(10%)
    if compliance_training >= 6:
        cts = 100
    elif compliance_training >= 4:
        cts = 80
    elif compliance_training >= 2:
        cts = 60
    else:
        cts = 30
    gov_score += cts * 0.10

    # 反腐败(15%)
    gov_score += anti_corruption * 0.15

    # ESG披露(15%)
    gov_score += esg_disclosure * 0.15

    # 审计独立(10%)
    gov_score += audit_independence * 0.10

    # 风险管理(15%)
    gov_score += risk_management * 0.15

    # 数据安全(10%)
    gov_score += data_security * 0.10

    # 所有权调整
    if ownership_type == "state":
        gov_score *= 1.05
    elif ownership_type == "foreign":
        gov_score *= 1.03

    gov_score = min(100, max(0, round(gov_score)))

    if gov_score >= 80:
        level, message = "优秀", "卓越的治理水平"
    elif gov_score >= 60:
        level, message = "良好", "规范的治理体系"
    else:
        level, message = "待改进", "需要完善治理结构"

    return {"score": gov_score, "level": level, "message": message}


def generate_recommendations(env: int, soc: int, gov: int) -> list[str]:
    """根据三维度评分生成改进建议"""
    recs = []
    if env < 60:
        recs.append("优化能源结构，提高能源使用效率")
        recs.append("加强废弃物管理和回收利用")
        recs.append("考虑使用清洁能源和可再生能源")
    if soc < 60:
        recs.append("加强员工培训和职业发展支持")
        recs.append("改善员工福利和工作环境")
        recs.append("增加社区投入和社会责任项目")
    if gov < 60:
        recs.append("完善公司治理结构，增加独立董事比例")
        recs.append("加强合规培训和反腐败制度建设")
        recs.append("提高信息披露透明度")
    return recs
