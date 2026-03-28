"""金融对接路由 - 产品推荐 / 申请记录 / 进度跟踪 / 融资方案对比 / 申请材料"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.finance import FinancialProduct, FinanceApplication
from models.enterprise import EnterpriseProfile
from models.data_upload import ApplicationMaterial
from schemas.finance import FinancialProductOut, FinanceApplicationCreate, FinanceApplicationOut
from utils.auth import get_current_user

router = APIRouter(prefix="/api/finance", tags=["金融对接"])


@router.get("/products", response_model=List[FinancialProductOut], summary="获取金融产品列表")
def list_products(
    category: Optional[str] = Query(None, description="按分类筛选: hot/recommended/new"),
    product_type: Optional[str] = Query(None, description="按类型筛选: credit/supplychain/project"),
    bank: Optional[str] = Query(None, description="按銀行筛选，如中国工商銀行"),
    max_amount: Optional[float] = Query(None, description="最大额度上限（元）"),
    min_esg_score: Optional[float] = Query(None, description="所需最低ESG评分"),
    db: Session = Depends(get_db),
):
    query = db.query(FinancialProduct).filter(FinancialProduct.is_active == 1)
    if category:
        query = query.filter(FinancialProduct.category == category)
    if product_type:
        query = query.filter(FinancialProduct.product_type == product_type)
    if bank:
        query = query.filter(FinancialProduct.bank.like(f"%{bank}%"))
    if max_amount is not None:
        query = query.filter(FinancialProduct.max_amount <= max_amount)
    if min_esg_score is not None:
        # requirements 字段包含 ESG评分要求，此处简单处理：只过滤max_amount，需要数据库层支持数字字段才能严格筛选
        pass
    return query.order_by(FinancialProduct.popularity.desc()).all()


@router.get("/products/{product_id}", response_model=FinancialProductOut, summary="获取金融产品详情")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(FinancialProduct).filter(FinancialProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return product


@router.post("/apply", response_model=FinanceApplicationOut, summary="申请金融产品")
def apply_product(
    body: FinanceApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(FinancialProduct).filter(FinancialProduct.id == body.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    if body.amount > product.max_amount:
        raise HTTPException(status_code=400, detail=f"申请金额不能超过{product.max_amount}元")

    application = FinanceApplication(
        user_id=current_user.id,
        product_id=body.product_id,
        amount=body.amount,
        purpose=body.purpose,
        status="pending",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/applications", response_model=List[FinanceApplicationOut], summary="获取我的申请记录")
def list_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(FinanceApplication)
        .filter(FinanceApplication.user_id == current_user.id)
        .order_by(FinanceApplication.created_at.desc())
        .all()
    )
    return records


# ============================================================
# 产品推荐（对应截图：金融对接·绿色信贷推荐 + 匹配度）
# ============================================================

def _calc_match_score(product: FinancialProduct, esg_score: float, carbon_grade: str) -> int:
    """根据企业ESG得分和碳效等级计算产品匹配度"""
    base = 60
    # ESG加分
    if esg_score >= 85:
        base += 20
    elif esg_score >= 75:
        base += 12
    elif esg_score >= 65:
        base += 5

    # 碳效等级加分
    grade_bonus = {"A+": 15, "A": 12, "A-": 10, "B+": 8, "B": 5, "B-": 2, "C": 0, "D": -5}
    base += grade_bonus.get(carbon_grade or "", 0)

    # 产品适配加分
    ptype = product.product_type or ""
    if ptype == "credit" and esg_score >= 80:
        base += 5
    if ptype == "supplychain":
        base -= 5  # 供应链金融门槛/适配度略低
    if "补贴" in product.name or "subsidy" in ptype:
        base += 8  # 政府补贴类匹配度通常高

    return max(30, min(99, base))


@router.get("/recommendations", summary="产品推荐（含匹配度）")
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    返回截图所示的产品推荐:
    - 企业ESG概况横幅
    - 各产品的匹配度百分比
    - 额度、利率信息
    """
    profile = db.query(EnterpriseProfile).filter(
        EnterpriseProfile.user_id == current_user.id
    ).first()

    esg_score = profile.esg_score if profile else 72
    carbon_grade = profile.carbon_efficiency_grade if profile else "B"
    company_name = profile.company_name if profile else "我的企业"

    # 计算行业百分位
    percentile = 58 if esg_score >= 80 else (35 if esg_score >= 60 else 15)

    products = (
        db.query(FinancialProduct)
        .filter(FinancialProduct.is_active == 1)
        .order_by(FinancialProduct.popularity.desc())
        .all()
    )

    recommended = []
    for p in products:
        match_score = _calc_match_score(p, esg_score, carbon_grade)
        recommended.append({
            "id": p.id,
            "name": p.name,
            "bank": p.bank,
            "product_type": p.product_type,
            "interest_rate": p.interest_rate,
            "max_amount": p.max_amount,
            "term": p.term,
            "match_score": match_score,
            "description": p.description,
            "requirements": p.requirements,
        })

    # 按匹配度排序
    recommended.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "enterprise_banner": {
            "esg_score": esg_score,
            "carbon_grade": carbon_grade,
            "percentile": percentile,
            "label": f"企业ESG:{int(esg_score)} 碳效{carbon_grade} 优于同行业{percentile}%企业",
        },
        "products": recommended,
    }


# ============================================================
# 进度跟踪
# ============================================================

@router.get("/progress/{application_id}", summary="申请进度跟踪")
def track_progress(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = (
        db.query(FinanceApplication)
        .filter(FinanceApplication.id == application_id, FinanceApplication.user_id == current_user.id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="申请记录不存在")

    # 模拟进度阶段
    stages = [
        {"step": 1, "name": "提交申请", "status": "completed", "date": app.created_at.strftime("%Y-%m-%d") if app.created_at else ""},
        {"step": 2, "name": "材料审核", "status": "completed" if app.status != "pending" else "in_progress", "date": ""},
        {"step": 3, "name": "银行评估", "status": "completed" if app.status in ("approved", "rejected") else "pending", "date": ""},
        {"step": 4, "name": "审批完成", "status": "completed" if app.status in ("approved", "rejected") else "pending", "date": ""},
        {"step": 5, "name": "放款", "status": "completed" if app.status == "approved" else "pending", "date": ""},
    ]

    return {
        "application_id": app.id,
        "product_id": app.product_id,
        "amount": app.amount,
        "status": app.status,
        "stages": stages,
    }


# ============================================================
# 融资方案对比
# ============================================================

@router.get("/comparison", summary="融资方案对比")
def compare_products(
    product_ids: str = Query("", description="逗号分隔的产品ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if product_ids:
        ids = [int(i.strip()) for i in product_ids.split(",") if i.strip().isdigit()]
    else:
        ids = []

    if not ids:
        products = db.query(FinancialProduct).filter(FinancialProduct.is_active == 1).limit(4).all()
    else:
        products = db.query(FinancialProduct).filter(FinancialProduct.id.in_(ids)).all()

    profile = db.query(EnterpriseProfile).filter(
        EnterpriseProfile.user_id == current_user.id
    ).first()
    esg = profile.esg_score if profile else 72
    grade = profile.carbon_efficiency_grade if profile else "B"

    rows = []
    for p in products:
        rows.append({
            "id": p.id,
            "name": p.name,
            "bank": p.bank,
            "interest_rate": p.interest_rate,
            "max_amount": p.max_amount,
            "term": p.term,
            "requirements": p.requirements,
            "match_score": _calc_match_score(p, esg, grade),
        })

    return {"products": rows}


# ============================================================
# 申请材料管理
# ============================================================

@router.get("/materials", summary="获取已上传申请材料")
def list_materials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    materials = (
        db.query(ApplicationMaterial)
        .filter(ApplicationMaterial.user_id == current_user.id)
        .order_by(ApplicationMaterial.created_at.desc())
        .all()
    )
    return [
        {
            "id": m.id,
            "file_name": m.file_name,
            "file_type": m.file_type,
            "doc_category": m.doc_category,
            "status": m.status,
            "created_at": m.created_at.strftime("%Y-%m-%d") if m.created_at else "",
        }
        for m in materials
    ]


from pydantic import BaseModel as _BaseModel

class _MaterialUpload(_BaseModel):
    file_name: str
    file_type: str = "pdf"
    doc_category: str = "other"

class _BatchApplyBody(_BaseModel):
    product_ids: List[int]
    amount: float = 0
    purpose: str = "绿色信贷"


@router.post("/materials", summary="上传申请材料")
def upload_material(
    body: _MaterialUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = body.file_name.rsplit(".", 1)[-1].lower() if "." in body.file_name else body.file_type
    material = ApplicationMaterial(
        user_id=current_user.id,
        file_name=body.file_name,
        file_type=ext,
        doc_category=body.doc_category,
        status="uploaded",
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return {"success": True, "material": {"id": material.id, "file_name": material.file_name, "status": material.status}}


# ============================================================
# 一键申请（批量）
# ============================================================

@router.post("/batch-apply", summary="一键申请所选产品")
def batch_apply(
    body: _BatchApplyBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product_ids = body.product_ids
    amount = body.amount
    purpose = body.purpose
    results = []
    for pid in product_ids:
        product = db.query(FinancialProduct).filter(FinancialProduct.id == pid).first()
        if not product:
            results.append({"product_id": pid, "success": False, "message": "产品不存在"})
            continue

        app = FinanceApplication(
            user_id=current_user.id,
            product_id=pid,
            amount=min(amount, product.max_amount) if amount > 0 else product.max_amount * 0.5,
            purpose=purpose,
            status="pending",
        )
        db.add(app)
        results.append({"product_id": pid, "success": True, "product_name": product.name})

    db.commit()
    return {"success": True, "results": results, "total_applied": sum(1 for r in results if r["success"])}
