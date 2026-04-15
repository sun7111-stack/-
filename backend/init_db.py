"""
数据库初始化脚本
运行方式: python init_db.py
功能:
  1. 创建所有表
  2. 插入初始种子数据（排放因子、行业基准、金融产品、政策、案例、演示用户）
"""
from database import engine, SessionLocal, Base

# 导入所有模型以注册到Base.metadata
from models.user import User
from models.carbon import EmissionFactor, IndustryBenchmark, CarbonRecord, EmissionFactorItem
from models.esg import EsgScore
from models.finance import FinancialProduct, FinanceApplication
from models.report import Report, Policy, CaseStudy, ContactMessage
from models.trace import DataTraceRecord
from models.enterprise import EnterpriseProfile, EnterpriseCertification, EnterpriseActivity
from models.data_upload import DataUpload, ApplicationMaterial
from models.flow import (
    EventStream,
    EvidenceChainRecord,
    EvidenceObject,
    EvidenceChainStep,
    EvidenceAnchor,
    EvidenceProof,
    TrustScoreRecord,
)
from models.report_record import ReportRecord
from models.analysis import AnalysisResult, AnalysisBreakdown, RiskResult
from models.data_pipeline import RawDataRecord, ParsedDataRecord, ActivityRecord
from models.factor_match_log import FactorMatchLog
from models.analysis_v2 import AnalysisResultV2Snapshot

from utils.auth import hash_password


def create_tables():
    """创建所有表"""
    print("正在创建数据表...")
    Base.metadata.create_all(bind=engine)
    print("数据表创建完成！")


def seed_data():
    """插入种子数据"""
    db = SessionLocal()
    try:
        # ---------- 1. 排放因子（对应前端 DataService.emissionFactors） ----------
        if db.query(EmissionFactor).count() == 0:
            print("插入排放因子数据...")
            factors = [
                EmissionFactor(name="electricity", name_cn="电力", factor=0.581, unit="kgCO2/kWh", source="中国电网平均"),
                EmissionFactor(name="coal", name_cn="煤炭", factor=2.64, unit="kgCO2/kg", source="国家标准"),
                EmissionFactor(name="natural_gas", name_cn="天然气", factor=1.89, unit="kgCO2/m³", source="国家标准"),
                EmissionFactor(name="gasoline", name_cn="汽油", factor=2.32, unit="kgCO2/L", source="国家标准"),
                EmissionFactor(name="diesel", name_cn="柴油", factor=2.68, unit="kgCO2/L", source="国家标准"),
                EmissionFactor(name="water", name_cn="自来水", factor=0.34, unit="kgCO2/m³", source="城市供水"),
                EmissionFactor(name="waste", name_cn="废弃物(填埋)", factor=0.85, unit="kgCO2/kg", source="填埋处理"),
                EmissionFactor(name="recycle", name_cn="废弃物(回收)", factor=0.12, unit="kgCO2/kg", source="回收处理"),
            ]
            db.add_all(factors)

        # ---------- 1.5 详细排放因子（轻量级参数关联数据库） ----------
        if db.query(EmissionFactorItem).count() == 0:
            print("插入轻量级参数关联数据库因子(EmissionFactorItem)...")
            demo_factors = [
                # electricity 电力
                EmissionFactorItem(activity_type="electricity", industry_type="general", region="全国", factor_value=0.5703, factor_unit="kgCO2e/kWh", source="生态环境部2022年全国电网平均排放因子", version="2025-demo", description="通用电力排放因子"),
                EmissionFactorItem(activity_type="electricity", industry_type="cross_border", region="华东", factor_value=0.5703, factor_unit="kgCO2e/kWh", source="生态环境部2022年全国电网平均排放因子", version="2025-demo", description="跨境电商华东仓储电力"),
                EmissionFactorItem(activity_type="electricity", industry_type="daily_goods", region="全国", factor_value=0.5703, factor_unit="kgCO2e/kWh", source="生态环境部2022年全国电网平均排放因子", version="2025-demo", description="日用百货店铺电力"),
                
                # natural_gas 天然气
                EmissionFactorItem(activity_type="natural_gas", industry_type="general", region="全国", factor_value=2.1622, factor_unit="kgCO2e/m3", source="2006年IPCC国家温室气体清单指南", version="2025-demo", description="通用天然气"),
                
                # diesel 柴油
                EmissionFactorItem(activity_type="diesel", industry_type="general", region="全国", factor_value=3.1605, factor_unit="kgCO2e/kg", source="2006年IPCC国家温室气体清单指南", version="2025-demo", description="通用柴油燃料"),
                EmissionFactorItem(activity_type="diesel", industry_type="cross_border", region="全国", factor_value=3.1605, factor_unit="kgCO2e/kg", source="2006年IPCC国家温室气体清单指南", version="2025-demo", description="跨境物流干线运输柴油"),
                
                # waste 废弃物
                EmissionFactorItem(activity_type="waste", industry_type="general", region="全国", factor_value=0.5, factor_unit="kgCO2e/kg", source="缺省估算数值", version="2025-demo", description="一般工业固废处理"),
                EmissionFactorItem(activity_type="waste", industry_type="daily_goods", region="全国", factor_value=0.35, factor_unit="kgCO2e/kg", source="缺省估算数值", version="2025-demo", description="日用品废弃物处理"),

                # air_logistics 航空物流 (特别是跨境电商场景)
                EmissionFactorItem(activity_type="air_logistics", industry_type="cross_border", region="全国", factor_value=0.15, factor_unit="kgCO2e/ton-km", source="VTT LIPASTO 估算数据", version="2025-demo", description="跨境电商国际航空货运"),

                # warehouse_energy 仓储能耗
                EmissionFactorItem(activity_type="warehouse_energy", industry_type="cross_border", region="华东", factor_value=45.0, factor_unit="kgCO2e/m2-year", source="行业均值测算", version="2025-demo", description="跨境海外仓/保税仓综合能耗"),
                EmissionFactorItem(activity_type="warehouse_energy", industry_type="daily_goods", region="全国", factor_value=30.0, factor_unit="kgCO2e/m2-year", source="行业均值测算", version="2025-demo", description="普通日用百货流转仓储"),

                # reverse_logistics 逆向物流 (退换货)
                EmissionFactorItem(activity_type="reverse_logistics", industry_type="cross_border", region="全国", factor_value=0.8, factor_unit="kgCO2e/order", source="行业均值测算", version="2025-demo", description="跨境电商高碳排退货物流"),
                EmissionFactorItem(activity_type="reverse_logistics", industry_type="daily_goods", region="全国", factor_value=0.2, factor_unit="kgCO2e/order", source="行业均值测算", version="2025-demo", description="境内普通日用品退货物流"),

                # packaging_waste 包装废弃物
                EmissionFactorItem(activity_type="packaging_waste", industry_type="cross_border", region="全国", factor_value=1.5, factor_unit="kgCO2e/kg", source="估算数值", version="2025-demo", description="跨境长途重度包装碳排"),
                EmissionFactorItem(activity_type="packaging_waste", industry_type="daily_goods", region="全国", factor_value=0.8, factor_unit="kgCO2e/kg", source="估算数值", version="2025-demo", description="日用百货轻量纸箱/塑料袋包装碳排"),
            ]
            db.add_all(demo_factors)

        # ---------- 2. 行业基准（对应前端 DataService.industryBenchmarks） ----------
        if db.query(IndustryBenchmark).count() == 0:
            print("插入行业基准数据...")
            benchmarks = [
                IndustryBenchmark(industry="ecommerce", industry_cn="电商", carbon_per_revenue=0.15, energy_metric=0.8, other_metric=0.65),
                IndustryBenchmark(industry="manufacture", industry_cn="制造业", carbon_per_revenue=0.85, energy_metric=1.2, other_metric=0.25),
                IndustryBenchmark(industry="logistics", industry_cn="物流", carbon_per_revenue=0.45, energy_metric=0.12, other_metric=0.75),
                IndustryBenchmark(industry="service", industry_cn="服务业", carbon_per_revenue=0.08, energy_metric=0.3, other_metric=0.9),
            ]
            db.add_all(benchmarks)

        # ---------- 3. 金融产品（对应前端 DataService.financialProducts） ----------
        if db.query(FinancialProduct).count() == 0:
            print("插入金融产品数据...")
            products = [
                FinancialProduct(
                    name="绿色信贷优惠包", product_type="credit", bank="中国工商银行",
                    interest_rate="LPR-50BP", max_amount=5000000, term="1-3年",
                    requirements="ESG评分≥70分",
                    description="专为绿色转型企业设计，利率优惠，审批快速",
                    popularity=95, category="hot"
                ),
                FinancialProduct(
                    name="绿色供应链金融", product_type="supplychain", bank="中国建设银行",
                    interest_rate="账期延长至90天", max_amount=3000000, term="按需",
                    requirements="供应链稳定，ESG评分≥75分",
                    description="优化供应链资金流，支持绿色供应链建设",
                    popularity=88, category="recommended"
                ),
                FinancialProduct(
                    name="碳减排项目贷款", product_type="project", bank="国家开发银行",
                    interest_rate="LPR-80BP", max_amount=10000000, term="3-5年",
                    requirements="有明确减排项目，技术可行",
                    description="支持企业节能减排技术改造项目",
                    popularity=92, category="hot"
                ),
                # 截图匹配的金融产品
                FinancialProduct(
                    name="兴业绿色低碳贷", product_type="credit", bank="兴业银行",
                    interest_rate="3.65%", max_amount=20000000, term="1-3年",
                    requirements="ESG评分≥75分，有减碳项目",
                    description="额度200-2000万，专注低碳转型企业",
                    popularity=92, category="hot"
                ),
                FinancialProduct(
                    name="建行碳效贷", product_type="credit", bank="建设银行",
                    interest_rate="3.45%", max_amount=10000000, term="1-3年",
                    requirements="碳效等级B+及以上",
                    description="额度100-1000万，碳效挂钩优惠",
                    popularity=88, category="recommended"
                ),
                FinancialProduct(
                    name="农商低碳补贴贷", product_type="subsidy", bank="农商银行",
                    interest_rate="贴息后2.2%", max_amount=5000000, term="1-2年",
                    requirements="获绿色工厂或低碳认证",
                    description="额度30-500万，政府贴息支持",
                    popularity=95, category="hot"
                ),
                FinancialProduct(
                    name="招商绿色供应链", product_type="supplychain", bank="招商银行",
                    interest_rate="3.80%", max_amount=8000000, term="按需",
                    requirements="供应链上下游企业",
                    description="额度50-800万，绿色供应链金融",
                    popularity=79, category="recommended"
                ),
            ]
            db.add_all(products)

        # ---------- 4. 政策法规（对应前端 DataService.policies） ----------
        if db.query(Policy).count() == 0:
            print("插入政策法规数据...")
            policies = [
                Policy(
                    title="双碳目标实施方案", agency="国家发改委",
                    publish_date="2023-06-15",
                    summary="明确2030年前碳达峰、2060年前碳中和的具体实施路径",
                    relevance="high"
                ),
                Policy(
                    title="中小企业绿色发展指导意见", agency="工信部",
                    publish_date="2023-08-22",
                    summary="支持中小企业绿色转型，提供财税、金融、技术等多方面支持",
                    relevance="high"
                ),
                Policy(
                    title="绿色信贷指引", agency="中国人民银行",
                    publish_date="2023-11-10",
                    summary="鼓励金融机构加大对绿色项目的信贷支持力度",
                    relevance="medium"
                ),
            ]
            db.add_all(policies)

        # ---------- 5. 客户案例（对应前端 DataService.caseStudies） ----------
        if db.query(CaseStudy).count() == 0:
            print("插入客户案例数据...")
            cases = [
                CaseStudy(
                    company="A电商公司", industry="ecommerce",
                    challenge="平台要求绿色商家认证，缺乏碳数据管理能力",
                    solution="使用碳融智核平台进行订单级碳核算，优化包装材料",
                    results={
                        "carbonReduction": 30,
                        "costSavings": 150000,
                        "esgScore": 85,
                        "timeSaved": 70,
                    },
                    testimonial="平台帮助我们轻松完成了绿色商家认证，订单量增长了20%"
                ),
                CaseStudy(
                    company="B制造工厂", industry="manufacture",
                    challenge="需要申请政府绿色技改补贴，但合规报告编制困难",
                    solution="通过平台自动生成符合要求的ESG报告，精准核算减排量",
                    results={
                        "subsidyObtained": 1200000,
                        "esgScore": 82,
                        "energySaved": 25,
                        "timeSaved": 85,
                    },
                    testimonial="成功申请到120万元补贴，平台的专业报告功不可没"
                ),
            ]
            db.add_all(cases)

        # ---------- 6. 演示用户（对应前端 DataService.users） ----------
        # 邮箱登录演示用户
        if not db.query(User).filter(User.email == "demo@carbon-ai.com").first():
            print("插入演示用户(邮箱)数据...")
            demo_user = User(
                email="demo@carbon-ai.com",
                password_hash=hash_password("demo123"),
                name="演示用户",
                company="演示科技有限公司",
                company_type="ecommerce",
                phone="13800001111",
            )
            db.add(demo_user)

        # 企业账号登录演示用户
        if not db.query(User).filter(User.enterprise_account == "LCZZ2024").first():
            print("插入演示用户(企业)数据...")
            enterprise_user = User(
                email="enterprise@carbon-ai.com",
                password_hash=hash_password("admin888"),
                name="绿创制造管理员",
                company="绿创智造科技有限公司",
                company_type="manufacture",
                phone="13900002222",
                enterprise_account="LCZZ2024",
            )
            db.add(enterprise_user)

        db.commit()

        # ---------- 7. 企业中心数据（对应截图中的企业中心页面）----------
        # 为企业用户创建企业 profile
        ent_user = db.query(User).filter(User.enterprise_account == "LCZZ2024").first()
        if ent_user and not db.query(EnterpriseProfile).filter(EnterpriseProfile.user_id == ent_user.id).first():
            print("插入企业中心数据...")
            profile = EnterpriseProfile(
                user_id=ent_user.id,
                company_name="绿创制造",
                industry="金属制品",
                annual_revenue=12000,          # 1.2亿 = 12000万
                employee_count=220,
                main_products="精密零部件",
                address="江苏省苏州市工业园区创新路88号",
                legal_person="张经理",
                established_date="2015-03-18",
                credit_code="91320500MA1EXAMPLE",
                contact_person="张经理",
                contact_phone="13900002222",
                total_carbon_emission=486,
                logistics_carbon_intensity=0.13,
                energy_intensity=0.21,
                esg_score=86,
                carbon_efficiency_grade="B+",
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)

            # 资质认证
            certs = [
                EnterpriseCertification(
                    enterprise_id=profile.id,
                    cert_name="ISO 14001 环境管理体系认证",
                    cert_type="iso",
                    cert_number="ISO14001-2024-00158",
                    issuing_authority="中国质量认证中心",
                    issue_date="2024-03-15",
                    expiry_date="2027-03-14",
                    status="valid",
                    description="环境管理体系达到国际标准",
                ),
                EnterpriseCertification(
                    enterprise_id=profile.id,
                    cert_name="绿色工厂认定",
                    cert_type="green",
                    cert_number="GF-JS-2024-0892",
                    issuing_authority="工业和信息化部",
                    issue_date="2024-06-01",
                    expiry_date="2026-05-31",
                    status="valid",
                    description="国家级绿色工厂认定",
                ),
                EnterpriseCertification(
                    enterprise_id=profile.id,
                    cert_name="碳足迹核查报告",
                    cert_type="esg",
                    cert_number="CFV-2024-JS-0356",
                    issuing_authority="上海环境能源交易所",
                    issue_date="2024-08-20",
                    expiry_date="2025-08-19",
                    status="valid",
                    description="2023年度企业碳足迹第三方核查",
                ),
            ]
            db.add_all(certs)

            # 最近活动
            activities = [
                EnterpriseActivity(enterprise_id=profile.id, action="login", title="管理员登录系统", detail="IP: 192.168.1.100"),
                EnterpriseActivity(enterprise_id=profile.id, action="upload", title="上传2024年Q4能耗数据", detail="电力、天然气、柴油消耗数据"),
                EnterpriseActivity(enterprise_id=profile.id, action="esg", title="完成ESG综合评估", detail="综合得分86分，等级B+"),
                EnterpriseActivity(enterprise_id=profile.id, action="report", title="生成ESG年度报告", detail="2024年度ESG综合报告"),
                EnterpriseActivity(enterprise_id=profile.id, action="finance", title="申请绿色信贷", detail="向兴业银行申请1200万绿色贷款"),
                EnterpriseActivity(enterprise_id=profile.id, action="edit", title="更新企业基本信息", detail="更新了联系人信息"),
            ]
            db.add_all(activities)

        # 为 demo 用户也创建一个 profile
        demo_user = db.query(User).filter(User.email == "demo@carbon-ai.com").first()
        if demo_user and not db.query(EnterpriseProfile).filter(EnterpriseProfile.user_id == demo_user.id).first():
            demo_profile = EnterpriseProfile(
                user_id=demo_user.id,
                company_name="演示科技有限公司",
                industry="电子商务",
                annual_revenue=3000,
                employee_count=50,
                main_products="数字化服务",
                total_carbon_emission=120,
                esg_score=72,
                carbon_efficiency_grade="B+",
            )
            db.add(demo_profile)

        # ---------- 8. 碳管理-数据上传种子数据 ----------
        ent_user = db.query(User).filter(User.enterprise_account == "LCZZ2024").first()
        if ent_user and db.query(DataUpload).filter(DataUpload.user_id == ent_user.id).count() == 0:
            print("插入数据上传记录...")
            uploads = [
                DataUpload(
                    user_id=ent_user.id, file_name="电费单(02.18)", file_type="invoice",
                    category="electricity", status="parsed",
                    parsed_data={"value": 1245, "unit": "kWh", "cost": 1245.00, "type": "工商业用电"},
                    period="2026-02"
                ),
                DataUpload(
                    user_id=ent_user.id, file_name="天然气账单(01.25)", file_type="bill",
                    category="gas", status="parsed",
                    parsed_data={"value": 850, "unit": "m³", "cost": 3400.00, "type": "天然气"},
                    period="2026-01"
                ),
                DataUpload(
                    user_id=ent_user.id, file_name="柴油加油发票(01.15)", file_type="invoice",
                    category="fuel", status="parsed",
                    parsed_data={"value": 320, "unit": "L", "cost": 2688.00, "type": "柴油"},
                    period="2026-01"
                ),
            ]
            db.add_all(uploads)

        # ---------- 9. 报告中心种子数据（对应截图中报告列表）----------
        import time as _time
        if ent_user and db.query(Report).filter(Report.user_id == ent_user.id).count() == 0:
            print("插入报告种子数据...")
            reports = [
                Report(
                    user_id=ent_user.id,
                    report_no=f"REPORT-{int(_time.time()*1000) % 100000000}",
                    template_type="esg",
                    title="2025年度ESG报告",
                    scenario="绿色信贷",
                    content={"sections": ["ESG概况", "环境绩效", "社会责任", "公司治理"]},
                    word_count=3200, charts_count=6, generation_time=22,
                    status="completed",
                ),
                Report(
                    user_id=ent_user.id,
                    report_no=f"REPORT-{int(_time.time()*1000) % 100000000 + 1}",
                    template_type="basic",
                    title="2025碳核算明细",
                    scenario="政府补贴",
                    content={"sections": ["企业概况", "核算边界", "排放量计算", "结果分析"]},
                    word_count=1800, charts_count=3, generation_time=15,
                    status="completed",
                ),
            ]
            db.add_all(reports)

        # ---------- 10. 金融申请材料种子数据 ----------
        if ent_user and db.query(ApplicationMaterial).filter(ApplicationMaterial.user_id == ent_user.id).count() == 0:
            print("插入申请材料种子数据...")
            materials = [
                ApplicationMaterial(
                    user_id=ent_user.id, file_name="营业执照.pdf",
                    file_type="pdf", doc_category="license", status="verified"
                ),
                ApplicationMaterial(
                    user_id=ent_user.id, file_name="财报.xlsx",
                    file_type="xlsx", doc_category="financial", status="verified"
                ),
            ]
            db.add_all(materials)

        # ---------- 11. 首页事件流种子数据 ----------
        if db.query(EventStream).count() == 0:
            print("插入事件流种子数据...")
            db.add_all([
                EventStream(enterprise_name="绿创制造", event_type="ocr_done", event_desc="OCR识别完成", event_status="done"),
                EventStream(enterprise_name="绿创制造", event_type="govern_done", event_desc="数据治理完成", event_status="done"),
                EventStream(enterprise_name="绿创制造", event_type="carbon_done", event_desc="碳核算完成", event_status="done"),
                EventStream(enterprise_name="绿创制造", event_type="risk_alert", event_desc="风控预警已生成", event_status="warning"),
                EventStream(enterprise_name="绿创制造", event_type="report_done", event_desc="报告预览生成完成", event_status="done"),
            ])

        # ---------- 12. 报告导出记录种子数据 ----------
        if ent_user and db.query(ReportRecord).filter(ReportRecord.user_id == ent_user.id).count() == 0:
            print("插入报告导出记录种子数据...")
            db.add(
                ReportRecord(
                    user_id=ent_user.id,
                    analysis_id="analysis-demo-001",
                    report_type="esg",
                    report_title="2025年度ESG报告",
                    export_status="exported",
                    file_path="/reports/2025-esg-demo.pdf",
                    report_context={"enterprise_name": "绿创制造", "analysis_date": "2026-04-14"},
                    report_preview={"summary": "示例导出记录", "risk_level": "medium"},
                )
            )

        # ---------- 13. 核算结果与风控结果种子数据 ----------
        if ent_user and db.query(AnalysisResult).filter(AnalysisResult.user_id == ent_user.id).count() == 0:
            print("插入核算结果种子数据...")
            ar = AnalysisResult(
                user_id=ent_user.id,
                enterprise_name="绿创制造",
                total_emission=486.0,
                carbon_intensity=0.13,
                industry_deviation=-0.08,
                risk_level="medium",
                major_source="electricity",
                advice_text="优先优化电力与运输环节排放。",
            )
            db.add(ar)
            db.flush()
            db.add_all([
                AnalysisBreakdown(analysis_id=ar.id, source_type="electricity", emission_value=260.0, proportion=53.5),
                AnalysisBreakdown(analysis_id=ar.id, source_type="diesel", emission_value=120.0, proportion=24.7),
                AnalysisBreakdown(analysis_id=ar.id, source_type="waste", emission_value=106.0, proportion=21.8),
            ])

        if ent_user and db.query(RiskResult).filter(RiskResult.user_id == ent_user.id).count() == 0:
            print("插入风控结果种子数据...")
            db.add(
                RiskResult(
                    user_id=ent_user.id,
                    analysis_id=1,
                    risk_score=64.5,
                    risk_level="medium",
                    risk_reason="碳强度偏高且物流波动较大",
                    risk_advice="加强运输排程与能耗管理，按月复盘风险阈值。",
                )
            )

        db.commit()
        print("种子数据插入完成！")
    except Exception as e:
        db.rollback()
        print(f"种子数据插入失败: {e}")
        raise
    finally:
        db.close()


def migrate_columns():
    """为已有数据库添加新字段"""
    from sqlalchemy import text, inspect
    inspector = inspect(engine)

    if "users" not in inspector.get_table_names():
        return

    # users 表新列
    existing_cols = {col["name"] for col in inspector.get_columns("users")}
    new_cols = {
        "phone": "VARCHAR(20) UNIQUE",
        "enterprise_account": "VARCHAR(100) UNIQUE",
        "failed_login_attempts": "INT DEFAULT 0",
        "locked_until": "DATETIME",
    }
    with engine.connect() as conn:
        for col_name, col_def in new_cols.items():
            if col_name not in existing_cols:
                print(f"添加列: users.{col_name}")
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
        conn.commit()

    # reports 表新列
    if "reports" in inspector.get_table_names():
        report_cols = {col["name"] for col in inspector.get_columns("reports")}
        report_new = {
            "scenario": "VARCHAR(100) DEFAULT ''",
            "review_comment": "TEXT",
        }
        with engine.connect() as conn:
            for col_name, col_def in report_new.items():
                if col_name not in report_cols:
                    print(f"添加列: reports.{col_name}")
                    conn.execute(text(f"ALTER TABLE reports ADD COLUMN {col_name} {col_def}"))
            # 更新 enum 添加 reviewing, approved 状态
            try:
                conn.execute(text(
                    "ALTER TABLE reports MODIFY COLUMN status "
                    "ENUM('draft','generating','completed','exported','reviewing','approved') DEFAULT 'draft'"
                ))
            except Exception:
                pass
            conn.commit()


if __name__ == "__main__":
    print("=" * 50)
    print("碳融智核平台 - 数据库初始化")
    print("=" * 50)
    create_tables()
    migrate_columns()
    seed_data()
    print("=" * 50)
    print("数据库初始化完成！")
    print("=" * 50)
    print("演示账号:")
    print("  邮箱登录:   demo@carbon-ai.com / demo123")
    print("  企业登录:   LCZZ2024 / admin888")
    print("  手机登录:   13800001111（验证码查看控制台）")
    print("=" * 50)
