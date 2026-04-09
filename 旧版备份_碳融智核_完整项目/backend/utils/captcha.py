"""图形验证码生成与校验工具"""
import random
import string
import time
import uuid
import base64

# 内存存储 {captcha_id: (text_upper, expire_timestamp)}
_store: dict[str, tuple[str, float]] = {}

EXPIRE_SECONDS = 300  # 5 分钟


def _clean():
    now = time.time()
    expired = [k for k, (_, exp) in _store.items() if now > exp]
    for k in expired:
        del _store[k]


def generate_captcha() -> tuple[str, str]:
    """
    生成图形验证码
    返回 (captcha_id, data_uri)  ——  data_uri 是 SVG Base64 编码
    验证码文本存在服务端，不返回给前端
    """
    _clean()
    text = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    # 排除易混淆字符
    text = text.replace("0", "X").replace("O", "Y").replace("I", "Z").replace("1", "W")
    cid = uuid.uuid4().hex[:16]
    _store[cid] = (text.upper(), time.time() + EXPIRE_SECONDS)
    svg = _render_svg(text)
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return cid, f"data:image/svg+xml;base64,{b64}"


def verify_captcha(captcha_id: str, user_input: str) -> bool:
    """校验图形验证码（一次有效）"""
    _clean()
    item = _store.pop(captcha_id, None)
    if item is None:
        return False
    text, expire = item
    if time.time() > expire:
        return False
    return user_input.strip().upper() == text


# ---------- SVG 渲染 ----------

def _render_svg(text: str) -> str:
    w, h = 120, 40
    colors = ["#2E7D32", "#1565C0", "#C62828", "#4527A0", "#E65100", "#00695C"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
        f'<rect width="{w}" height="{h}" fill="#f5f5f5" rx="4"/>'
    ]
    # 干扰线
    for _ in range(5):
        x1, y1 = random.randint(0, w), random.randint(0, h)
        x2, y2 = random.randint(0, w), random.randint(0, h)
        c = random.choice(colors)
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{c}" stroke-width="1" opacity="0.3"/>'
        )
    # 干扰点
    for _ in range(30):
        cx, cy = random.randint(0, w), random.randint(0, h)
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="1.5" fill="{random.choice(colors)}" opacity="0.4"/>'
        )
    # 文字
    for i, ch in enumerate(text):
        x = 12 + i * 26
        y = random.randint(24, 32)
        rot = random.randint(-20, 20)
        c = random.choice(colors)
        parts.append(
            f'<text x="{x}" y="{y}" font-size="22" font-family="monospace" '
            f'font-weight="bold" fill="{c}" '
            f'transform="rotate({rot},{x},{y})">{ch}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)
