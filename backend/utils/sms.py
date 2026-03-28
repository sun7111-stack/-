"""短信验证码工具（开发模拟）"""
import random
import time

# 内存存储 {phone: (code, expire_timestamp)}
_store: dict[str, tuple[str, float]] = {}

# 发送频率限制 {phone: last_send_timestamp}
_rate: dict[str, float] = {}

EXPIRE_SECONDS = 300   # 5 分钟有效
RATE_LIMIT = 60        # 最短间隔 60 秒


def send_sms_code(phone: str) -> tuple[bool, str, str]:
    """
    发送短信验证码（模拟）。
    返回 (success, message, code)
    code 仅在开发环境返回给前端方便测试，生产环境应隐藏。
    """
    now = time.time()

    # 频率限制
    last = _rate.get(phone, 0)
    if now - last < RATE_LIMIT:
        remaining = int(RATE_LIMIT - (now - last))
        return False, f"发送过于频繁，请{remaining}秒后再试", ""

    code = "".join(random.choices("0123456789", k=6))
    _store[phone] = (code, now + EXPIRE_SECONDS)
    _rate[phone] = now

    # 模拟发送：打印到控制台
    print(f"\n{'='*40}")
    print(f"[短信模拟] 手机号: {phone}")
    print(f"[短信模拟] 验证码: {code}")
    print(f"[短信模拟] 有效期: {EXPIRE_SECONDS // 60} 分钟")
    print(f"{'='*40}\n")

    return True, "验证码已发送", code


def verify_sms_code(phone: str, code: str) -> bool:
    """校验短信验证码（一次有效）"""
    item = _store.get(phone)
    if item is None:
        return False
    stored_code, expire = item
    if time.time() > expire:
        _store.pop(phone, None)
        return False
    if stored_code != code.strip():
        return False
    _store.pop(phone, None)
    return True
