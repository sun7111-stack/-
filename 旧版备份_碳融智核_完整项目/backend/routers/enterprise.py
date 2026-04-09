"""企业中心路由 —— 基本信息 / 资质认证 / 数据权限 / 账号设置 / 最近活动"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.user import User
from models.enterprise import EnterpriseProfile, EnterpriseCertification, EnterpriseActivity
from schemas.enterprise import (
    EnterpriseProfileResponse, EnterpriseProfileUpdate, EnterpriseDashboard,
    CertificationCreate, CertificationUpdate, CertificationResponse,
    ActivityResponse, AccountSettingsUpdate, AccountSettingsResponse,
    DataPermissionResponse,
)
from utils.auth import get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/enterprise", tags=["企业中心"])


# ---------- 工具函数 ----------

def _get_or_create_profile(user: User, db: Session) -> EnterpriseProfile:
    """获取企业 Profile，不存在则自动创建"""
    profile = db.query(EnterpriseProfile).filter(EnterpriseProfile.user_id == user.id).first()
    if not profile:
        profile = EnterpriseProfile(
            user_id=user.id,
            company_name=user.company or user.name,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _format_revenue(wan_yuan: float) -> str:
    """将万元格式化为可读文本：12000 → '1.2亿'"""
    if wan_yuan >= 10000:
        return f"{wan_yuan / 10000:.1f}亿"
    elif wan_yuan >= 1:
        return f"{wan_yuan:.0f}万"
    else:
        return "0"


def _calc_carbon_grade(esg_score: float, carbon_emission: float, revenue: float) -> str:
    """根据ESG得分和碳效（碳排放/营收）计算碳效等级"""
    carbon_intensity = carbon_emission / revenue if revenue else 999
    if esg_score >= 90 and carbon_intensity < 0.02:
        return "A+"
    elif esg_score >= 90:
        return "A"
    elif esg_score >= 85 and carbon_intensity < 0.03:
        return "A-"
    elif esg_score >= 80 and carbon_intensity < 0.05:
        return "B+"
    elif esg_score >= 70:
        return "B"
    elif esg_score >= 60:
        return "B-"
    elif esg_score >= 40:
        return "C"
    else:
        return "D"


def _record_activity(db: Session, enterprise_id: int, action: str, title: str, detail: str = ""):
    """记录企业活动"""
    act = EnterpriseActivity(
        enterprise_id=enterprise_id,
        action=action,
        title=title,
        detail=detail,
    )
    db.add(act)
    db.commit()


# ============================================================
# 企业概览仪表盘
# ============================================================

@router.get("/dashboard", response_model=EnterpriseDashboard, summary="企业概览仪表盘")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _get_or_create_profile(current_user, db)

    # 动态计算碳效等级
    grade = _calc_carbon_grade(
        profile.esg_score,
        profile.total_carbon_emission,
        profile.annual_revenue
    )
    if grade != profile.carbon_efficiency_grade:
        profile.carbon_efficiency_grade = grade
        db.commit()

    return EnterpriseDashboard(
        company_name=profile.company_name,
        annual_revenue=profile.annual_revenue,
        annual_revenue_display=_format_revenue(profile.annual_revenue),
        total_carbon_emission=profile.total_carbon_emission,
        esg_score=profile.esg_score,
        carbon_efficiency_grade=profile.carbon_efficiency_grade or "N/A",
        logistics_carbon_intensity=profile.logistics_carbon_intensity,
        energy_intensity=profile.energy_intensity,
        industry=profile.industry,
        employee_count=profile.employee_count,
        main_products=profile.main_products,
    )


# ============================================================
# 基本信息
# ============================================================

@router.get("/profile", response_model=EnterpriseProfileResponse, summary="获取企业基本信息")
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_or_create_profile(current_user, db)


@router.put("/profile", response_model=EnterpriseProfileResponse, summary="更新企业基本信息")
def update_profile(
    body: EnterpriseProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _get_or_create_profile(current_user, db)

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)

    _record_activity(db, profile.id, "edit", "更新企业基本信息",
                     f"修改了 {', '.join(update_data.keys())}")
    return profile


# ============================================================
# 资质认证
# ============================================================

@router.get("/certifications", response_model=List[CertificationResponse], summary="获取资质认证列表")
def get_certifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _get_or_create_profile(current_user, db)
    certs = db.query(EnterpriseCertification).filter(
        EnterpriseCertification.enterprise_id == profile.id
    ).order_by(EnterpriseCertification.created_at.desc()).all()
    return certs


@router.post("/certifications", response_model=CertificationResponse, summary="添加资质认证")
def create_certification(
    body: CertificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _get_or_create_profile(current_user, db)
    cert = EnterpriseCertification(
        enterprise_id=profile.id,
        **body.model_dump(),
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)

    _record_activity(db, profile.id, "upload", f"添加资质认证: {body.cert_name}")
    return cert


@router.put("/certifications/{cert_id}", response_model=CertificationResponse, summary="更新资质认证")
def update_certification(
    cert_id: int,
    body: CertificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _get_or_create_profile(current_user, db)
    cert = db.query(EnterpriseCertification).filter(
        EnterpriseCertification.id == cert_id,
        EnterpriseCertification.enterprise_id == profile.id,
    ).first()
    if not cert:
        raise HTTPException(status_code=404, detail="认证记录不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cert, key, value)
    db.commit()
    db.refresh(cert)
    return cert


@router.delete("/certifications/{cert_id}", summary="删除资质认证")
def delete_certification(
    cert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _get_or_create_profile(current_user, db)
    cert = db.query(EnterpriseCertification).filter(
        EnterpriseCertification.id == cert_id,
        EnterpriseCertification.enterprise_id == profile.id,
    ).first()
    if not cert:
        raise HTTPException(status_code=404, detail="认证记录不存在")

    name = cert.cert_name
    db.delete(cert)
    db.commit()
    _record_activity(db, profile.id, "edit", f"删除资质认证: {name}")
    return {"detail": "已删除"}


# ============================================================
# 数据权限
# ============================================================

@router.get("/permissions", response_model=DataPermissionResponse, summary="获取数据权限")
def get_permissions(
    current_user: User = Depends(get_current_user),
):
    """返回当前用户的数据权限（简化版 — 所有已登录用户拥有完整权限）"""
    is_enterprise = bool(current_user.enterprise_account)
    return DataPermissionResponse(
        can_view_carbon=True,
        can_edit_carbon=True,
        can_view_esg=True,
        can_edit_esg=True,
        can_generate_report=True,
        can_apply_finance=True,
        can_manage_users=is_enterprise,
        role="enterprise_admin" if is_enterprise else "user",
        data_scope="all",
    )


# ============================================================
# 账号设置
# ============================================================

@router.get("/account", response_model=AccountSettingsResponse, summary="获取账号信息")
def get_account(
    current_user: User = Depends(get_current_user),
):
    return AccountSettingsResponse.model_validate(current_user)


@router.put("/account", response_model=AccountSettingsResponse, summary="更新账号设置")
def update_account(
    body: AccountSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.name is not None:
        current_user.name = body.name
    if body.phone is not None:
        dup = db.query(User).filter(User.phone == body.phone, User.id != current_user.id).first()
        if dup:
            raise HTTPException(status_code=400, detail="该手机号已被其他账户绑定")
        current_user.phone = body.phone
    if body.email is not None:
        dup = db.query(User).filter(User.email == body.email, User.id != current_user.id).first()
        if dup:
            raise HTTPException(status_code=400, detail="该邮箱已被其他账户使用")
        current_user.email = body.email
    if body.position is not None:
        current_user.position = body.position
    # 修改密码
    if body.new_password:
        if not body.old_password:
            raise HTTPException(status_code=400, detail="修改密码需要提供旧密码")
        if not current_user.password_hash or not verify_password(body.old_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="旧密码错误")
        current_user.password_hash = hash_password(body.new_password)

    db.commit()
    db.refresh(current_user)

    # 记录活动
    profile = db.query(EnterpriseProfile).filter(EnterpriseProfile.user_id == current_user.id).first()
    if profile:
        _record_activity(db, profile.id, "edit", "更新账号设置")

    return AccountSettingsResponse.model_validate(current_user)


# ============================================================
# 最近活动
# ============================================================

@router.get("/activities", response_model=List[ActivityResponse], summary="获取最近活动")
def get_activities(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _get_or_create_profile(current_user, db)
    activities = db.query(EnterpriseActivity).filter(
        EnterpriseActivity.enterprise_id == profile.id
    ).order_by(EnterpriseActivity.created_at.desc()).limit(limit).all()
    return activities
