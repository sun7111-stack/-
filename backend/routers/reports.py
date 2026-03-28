"""报告、政策、案例、联系路由"""
import time
import random
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.report import Report, Policy, CaseStudy, ContactMessage
from schemas.report import (
    ReportGenerate,
    ReportOut,
    ReportReview,
    CustomTemplate,
    PolicyOut,
    CaseStudyOut,
    ContactMessageCreate,
    ContactMessageOut,
    ApiResponse,
)
from utils.auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api", tags=["报告与数据"])

# ============== 报告模板配置（与前端DataService.reportTemplates一致） ==============
REPORT_TEMPLATES = {
    "basic": {
        "name": "基础碳核算报告",
        "description": "符合国家基本要求的碳核算报告",
        "sections": ["企业概况", "核算边界", "排放源识别", "活动数据", "排放量计算", "结果分析"],
        "estimated_time": 15,
        "word_count": 1500,
        "charts": 3,
    },
    "esg": {
        "name": "ESG综合报告",
        "description": "环境、社会、治理多维度综合分析报告",
        "sections": ["ESG概况", "环境绩效", "社会责任", "公司治理", "风险管理", "改进建议"],
        "estimated_time": 25,
        "word_count": 3000,
        "charts": 6,
    },
    "finance": {
        "name": "绿色金融申请报告",
        "description": "适配银行绿色信贷申请要求的专业报告",
        "sections": ["企业基本信息", "融资需求", "绿色项目介绍", "ESG表现", "减排效益", "还款保障"],
        "estimated_time": 20,
        "word_count": 2500,
        "charts": 4,
    },
}


# ========== 报告 ==========

@router.get("/reports/templates", summary="获取报告模板列表")
def list_report_templates():
    return REPORT_TEMPLATES


@router.post("/reports/generate", response_model=ReportOut, summary="生成报告")
def generate_report(
    body: ReportGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = REPORT_TEMPLATES.get(body.template_type)
    if not template:
        raise HTTPException(status_code=400, detail="无效的报告模板类型")

    report_no = f"REPORT-{int(time.time() * 1000) % 100000000}"
    gen_time = random.randint(template["estimated_time"], template["estimated_time"] + 10)
    word_count = template["word_count"] + random.randint(0, 500)

    report = Report(
        user_id=current_user.id,
        report_no=report_no,
        template_type=body.template_type,
        title=body.title or f"{template['name']} - {time.strftime('%Y-%m-%d')}",
        scenario=body.scenario or "",
        content={
            "sections": template["sections"],
            "description": template["description"],
        },
        word_count=word_count,
        charts_count=template["charts"],
        generation_time=gen_time,
        status="completed",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports", response_model=List[ReportOut], summary="获取报告历史")
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .limit(50)
        .all()
    )
    return records


# ========== 政策法规 ==========

@router.get("/policies", response_model=List[PolicyOut], summary="获取政策法规列表")
def list_policies(db: Session = Depends(get_db)):
    return db.query(Policy).order_by(Policy.publish_date.desc()).all()


# ========== 客户案例 ==========

@router.get("/cases", response_model=List[CaseStudyOut], summary="获取客户案例")
def list_cases(db: Session = Depends(get_db)):
    return db.query(CaseStudy).all()


# ========== 联系我们（咨询） ==========

@router.post("/contact", response_model=ContactMessageOut, summary="提交咨询消息")
def submit_contact(
    body: ContactMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    msg = ContactMessage(
        user_id=current_user.id if current_user else None,
        name=body.name,
        email=body.email,
        phone=body.phone,
        company=body.company,
        company_type=body.company_type or "",
        message=body.message,
        msg_type=body.msg_type,
        status="pending",
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@router.post("/reports/{report_id}/save-cloud", summary="保存报告至云端")
def save_report_to_cloud(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    # 模拟云端保存操作（实际项目可对接OSS等存储服务）
    return {"success": True, "message": "报告已保存至云端", "report_id": report_id}


# ============================================================
# 我的报告（增强版，含场景）
# ============================================================

@router.get("/reports/my-reports", summary="我的报告（含场景信息）")
def my_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """返回截图所示的 我的报告 列表"""
    records = (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": r.id,
            "report_no": r.report_no,
            "title": r.title,
            "template_type": r.template_type,
            "scenario": getattr(r, "scenario", "") or "",
            "status": r.status,
            "word_count": r.word_count,
            "charts_count": r.charts_count,
            "review_comment": getattr(r, "review_comment", "") or "",
            "created_at": r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
        }
        for r in records
    ]


# ============================================================
# 报告审核
# ============================================================

@router.get("/reports/review-list", summary="待审核报告列表")
def review_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .filter(Report.status.in_(["completed", "reviewing"]))
        .order_by(Report.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "title": r.title,
            "status": r.status,
            "review_comment": getattr(r, "review_comment", "") or "",
            "created_at": r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
        }
        for r in records
    ]


@router.put("/reports/{report_id}/review", summary="审核报告")
def review_report(
    report_id: int,
    body: ReportReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    report.status = body.status
    report.review_comment = body.comment
    db.commit()
    db.refresh(report)
    return {"success": True, "message": f"报告已{body.status}", "status": report.status}


# ============================================================
# 自定义模板
# ============================================================

# 内存存储自定义模板（实际项目应持久化到DB）
_custom_templates = {}


@router.get("/reports/custom-templates", summary="获取自定义模板列表")
def list_custom_templates(
    current_user: User = Depends(get_current_user),
):
    user_templates = _custom_templates.get(current_user.id, [])
    return {"templates": user_templates, "count": len(user_templates)}


@router.post("/reports/custom-templates", summary="创建自定义模板")
def create_custom_template(
    body: CustomTemplate,
    current_user: User = Depends(get_current_user),
):
    if current_user.id not in _custom_templates:
        _custom_templates[current_user.id] = []

    tpl = {
        "id": len(_custom_templates[current_user.id]) + 1,
        "name": body.name,
        "description": body.description,
        "sections": body.sections or ["企业概况", "数据分析", "结论建议"],
        "scenario": body.scenario,
    }
    _custom_templates[current_user.id].append(tpl)
    return {"success": True, "template": tpl}


# ============================================================
# 报告详情（放在所有 /reports/xxx 之后，避免路由冲突）
# ============================================================

@router.get("/reports/{report_id}", response_model=ReportOut, summary="获取报告详情")
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report
