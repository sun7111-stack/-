"""用户认证路由 —— 多方式登录 / 注册 / 验证码 / 访客预览"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.user import (
    UserRegister, UserLogin, TokenResponse, UserInfo,
    UserProfileUpdate, PhoneLoginRequest, SendSmsRequest,
    EnterpriseLoginRequest, CaptchaResponse, SmsCodeResponse,
)
from utils.auth import hash_password, verify_password, create_access_token, get_current_user
from utils.captcha import generate_captcha, verify_captcha
from utils.sms import send_sms_code, verify_sms_code

router = APIRouter(prefix="/api/auth", tags=["用户认证"])

# ---------- 安全常量 ----------
MAX_FAILED_ATTEMPTS = 3
LOCKOUT_MINUTES = 15


def _check_lockout(user: User):
    """检查账户是否被锁定"""
    if user.locked_until and user.locked_until.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
        remaining = int((user.locked_until.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds() / 60) + 1
        raise HTTPException(
            status_code=423,
            detail=f"账户已锁定，请{remaining}分钟后再试（连续{MAX_FAILED_ATTEMPTS}次登录失败）"
        )


def _record_failure(user: User, db: Session):
    """记录登录失败"""
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        from datetime import timedelta
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
        user.failed_login_attempts = 0
        db.commit()
        raise HTTPException(
            status_code=423,
            detail=f"连续{MAX_FAILED_ATTEMPTS}次登录失败，账户已锁定{LOCKOUT_MINUTES}分钟"
        )
    db.commit()


def _clear_failure(user: User, db: Session):
    """登录成功，清除失败计数"""
    if user.failed_login_attempts or user.locked_until:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()


# ============================================================
# 图形验证码
# ============================================================

@router.get("/captcha", response_model=CaptchaResponse, summary="获取图形验证码")
def get_captcha():
    cid, image = generate_captcha()
    return CaptchaResponse(captcha_id=cid, captcha_image=image)


# ============================================================
# 短信验证码
# ============================================================

@router.post("/sms-code", response_model=SmsCodeResponse, summary="发送短信验证码")
def request_sms_code(body: SendSmsRequest, db: Session = Depends(get_db)):
    # 1. 校验图形验证码
    if not verify_captcha(body.captcha_id, body.captcha):
        raise HTTPException(status_code=400, detail="图形验证码错误或已过期")

    # 2. 校验手机号格式
    phone = body.phone.strip()
    if not phone or len(phone) < 11:
        raise HTTPException(status_code=400, detail="请输入正确的手机号")

    # 3. 发送
    success, msg, code = send_sms_code(phone)
    if not success:
        raise HTTPException(status_code=429, detail=msg)

    return SmsCodeResponse(success=True, message=msg, code=code)


# ============================================================
# 手机号登录（自动注册）
# ============================================================

@router.post("/login/phone", response_model=TokenResponse, summary="手机号+验证码登录")
def login_by_phone(body: PhoneLoginRequest, db: Session = Depends(get_db)):
    phone = body.phone.strip()

    # 1. 校验短信验证码
    if not verify_sms_code(phone, body.sms_code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    # 2. 查找/创建用户
    user = db.query(User).filter(User.phone == phone).first()
    if user:
        _check_lockout(user)
        _clear_failure(user, db)
    else:
        # 自动注册
        user = User(
            phone=phone,
            name=f"用户{phone[-4:]}",
            company="",
            company_type="ecommerce",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserInfo.model_validate(user))


# ============================================================
# 企业账号登录
# ============================================================

@router.post("/login/enterprise", response_model=TokenResponse, summary="企业账号+密码登录")
def login_by_enterprise(body: EnterpriseLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.enterprise_account == body.account).first()
    if not user:
        raise HTTPException(status_code=401, detail="企业账号不存在")

    _check_lockout(user)

    if not user.password_hash or not verify_password(body.password, user.password_hash):
        _record_failure(user, db)
        remaining = MAX_FAILED_ATTEMPTS - (user.failed_login_attempts or 0)
        raise HTTPException(
            status_code=401,
            detail=f"密码错误，还可尝试{remaining}次"
        )

    _clear_failure(user, db)
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserInfo.model_validate(user))


# ============================================================
# 邮箱登录（原有，增加锁定逻辑）
# ============================================================

@router.post("/login", response_model=TokenResponse, summary="邮箱+密码登录")
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码错误，请重试")

    _check_lockout(user)

    if not verify_password(body.password, user.password_hash):
        _record_failure(user, db)
        remaining = MAX_FAILED_ATTEMPTS - (user.failed_login_attempts or 0)
        raise HTTPException(
            status_code=401,
            detail=f"邮箱或密码错误，还可尝试{remaining}次"
        )

    _clear_failure(user, db)
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserInfo.model_validate(user))


# ============================================================
# 注册（原有）
# ============================================================

@router.post("/register", response_model=TokenResponse, summary="用户注册")
def register(body: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已被注册，请使用其他邮箱")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        company=body.company or "",
        company_type=body.company_type or "ecommerce",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserInfo.model_validate(user))


# ============================================================
# 获取 / 更新个人信息
# ============================================================

@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    return UserInfo.model_validate(current_user)


@router.put("/me", response_model=UserInfo, summary="更新个人信息")
def update_me(
    body: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.name is not None:
        current_user.name = body.name
    if body.company is not None:
        current_user.company = body.company
    if body.company_type is not None:
        current_user.company_type = body.company_type
    if body.position is not None:
        current_user.position = body.position
    if body.phone is not None:
        # 检查手机号唯一性
        dup = db.query(User).filter(User.phone == body.phone, User.id != current_user.id).first()
        if dup:
            raise HTTPException(status_code=400, detail="该手机号已被其他账户绑定")
        current_user.phone = body.phone
    db.commit()
    db.refresh(current_user)
    return UserInfo.model_validate(current_user)


# ============================================================
# 访客预览（无需登录）
# ============================================================

@router.get("/visitor-preview", summary="访客预览（无需登录）")
def visitor_preview():
    """返回访客可预览的平台功能概览和成功案例"""
    return {
        "features": [
            {"icon": "file-alt", "name": "智能采集", "desc": "OCR+NLP自动识别票据，数据采集效率提升90%"},
            {"icon": "calculator", "name": "自动核算", "desc": "一键碳排放核算，覆盖Scope 1/2/3全范围"},
            {"icon": "leaf", "name": "ESG评分", "desc": "环境·社会·治理三维度智能评分，对标国际标准"},
            {"icon": "hand-holding-usd", "name": "绿色融资", "desc": "精准匹配绿色金融产品，利率优惠可达LPR-80BP"},
        ],
        "success_case": {
            "company": "绿创制造",
            "result": "获兴业1200万绿色贷",
            "detail": "通过碳融智核ESG评分认证，成功获得兴业银行1200万绿色信贷额度"
        },
        "partners": ["建设银行", "兴业银行", "京东物流", "天猫", "中国循环经济协会"],
        "advantages": ["低成本", "高效率", "全链路"],
        "security": "双重验证 · 新用户极速认证 · 失败3次锁定15分钟"
    }
