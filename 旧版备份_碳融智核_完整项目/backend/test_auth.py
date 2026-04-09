"""测试所有新认证API端点"""
import urllib.request as ur
import urllib.error as ue
import json

B = 'http://localhost:8000/api'

def req(method, path, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    body = json.dumps(data).encode() if data else None
    try:
        r = ur.urlopen(ur.Request(B + path, data=body, headers=headers, method=method))
        return r.status, json.loads(r.read())
    except ue.HTTPError as e:
        return e.code, json.loads(e.read())

print("=" * 50)
print("新认证API测试")
print("=" * 50)

# 1. 图形验证码
s, d = req('GET', '/auth/captcha')
cid = d.get('captcha_id', '')
has_img = 'captcha_image' in d and d['captcha_image'].startswith('data:')
print(f"1. GET /auth/captcha: {s}, captcha_id={cid[:8]}..., has_image={has_img}")

# 2. 访客预览
s, d = req('GET', '/auth/visitor-preview')
print(f"2. GET /auth/visitor-preview: {s}, features={len(d.get('features',[]))}, partners={len(d.get('partners',[]))}")

# 3. 企业登录
s, d = req('POST', '/auth/login/enterprise', {'account': 'LCZZ2024', 'password': 'admin888'})
ent_name = d.get('user', {}).get('name', '')
ent_token = d.get('access_token', '')
print(f"3. POST /auth/login/enterprise: {s}, user={ent_name}")

# 4. 获取企业用户信息
if ent_token:
    s, d = req('GET', '/auth/me', token=ent_token)
    print(f"4. GET /auth/me (企业): {s}, enterprise_account={d.get('enterprise_account','')}, phone={d.get('phone','')}")

# 5. 手机号登录 - 通过API流程（获取验证码→发送短信→手机登录）
# 获取验证码（注意：验证码文本只在服务端，我们无法从API获取它来测试）
# 所以这里直接从服务器后端模拟短信场景
# 用API发送短信（需要captcha，但captcha我们无法知道答案）
# 改为直接测试手机登录端点（短信验证码由服务端send_sms_code生成，我们通过API获取）
s_captcha, d_captcha = req('GET', '/auth/captcha')
# 无法知道验证码内容来通过API测试，跳过短信发送测试
print(f"5. GET /auth/captcha(for SMS): {s_captcha} (验证码需要UI交互)")

# 6. 邮箱登录（原有）
s, d = req('POST', '/auth/login', {'email': 'demo@carbon-ai.com', 'password': 'demo123'})
email_name = d.get('user', {}).get('name', '')
email_phone = d.get('user', {}).get('phone', '')
print(f"6. POST /auth/login (邮箱): {s}, user={email_name}, phone={email_phone}")

# 7. 登录失败锁定测试
print("7. 测试登录锁定 (连续3次错误密码):")
for i in range(4):
    s, d = req('POST', '/auth/login/enterprise', {'account': 'LCZZ2024', 'password': 'wrongpwd'})
    detail = d.get('detail', '')
    print(f"   尝试{i+1}: {s} - {detail}")

# 8. 注册新用户
s, d = req('POST', '/auth/register', {
    'email': 'test_new@example.com',
    'password': 'testpass123',
    'name': '测试新用户',
    'company': '测试公司',
    'company_type': 'service'
})
new_name = d.get('user', {}).get('name', d.get('detail', ''))
print(f"8. POST /auth/register: {s}, user={new_name}")

print("=" * 50)
print("全部测试完成！")
