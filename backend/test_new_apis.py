"""测试所有新增 API 端点"""
import requests, json, sys

BASE = "http://localhost:8000/api"
passed = 0
failed = 0

def test(name, method, url, expected_status=200, body=None, token=None):
    global passed, failed
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            r = requests.post(url, json=body, headers=headers, timeout=10)
        elif method == "PUT":
            headers["Content-Type"] = "application/json"
            r = requests.put(url, json=body, headers=headers, timeout=10)
        elif method == "DELETE":
            r = requests.delete(url, headers=headers, timeout=10)
        
        if r.status_code == expected_status:
            passed += 1
            print(f"  ✅ {name} ({r.status_code})")
            return r.json() if r.text else None
        else:
            failed += 1
            print(f"  ❌ {name} 期望 {expected_status} 得到 {r.status_code}")
            try:
                print(f"     {r.json()}")
            except:
                print(f"     {r.text[:200]}")
            return None
    except Exception as e:
        failed += 1
        print(f"  ❌ {name} 异常: {e}")
        return None

# ---- 登录获取 Token ----
print("\n=== 登录 ===")
data = test("企业登录", "POST", f"{BASE}/auth/login/enterprise", 200, {
    "account": "LCZZ2024",
    "password": "admin888"
})
if not data:
    print("登录失败，无法继续测试")
    sys.exit(1)
token = data["access_token"]

# ========================
# 1. 碳管理模块
# ========================
print("\n=== 碳管理模块 ===")
test("获取上传列表", "GET", f"{BASE}/carbon-manage/uploads", 200, token=token)
test("手动录入", "POST", f"{BASE}/carbon-manage/manual-entry", 200, {
    "category": "electricity",
    "value": 1500,
    "unit": "kWh",
    "period": "2026-02",
    "cost": 1350.0,
    "note": "测试录入"
}, token=token)
test("能耗分析", "GET", f"{BASE}/carbon-manage/energy-analysis", 200, token=token)

# 再次获取列表（应该多了一条）
uploads = test("上传列表(含手动)", "GET", f"{BASE}/carbon-manage/uploads", 200, token=token)

# ========================
# 2. ESG 评分模块
# ========================
print("\n=== ESG评分模块 ===")
detail = test("评分详情", "GET", f"{BASE}/esg/score-detail", 200, token=token)
if detail:
    print(f"     总分: {detail.get('total_score')}, 等级: {detail.get('level')}")

test("对标分析", "GET", f"{BASE}/esg/benchmark", 200, token=token)
test("改进计划", "GET", f"{BASE}/esg/improvement-plans", 200, token=token)
test("历史趋势", "GET", f"{BASE}/esg/trends", 200, token=token)

# ========================
# 3. 报告中心模块
# ========================
print("\n=== 报告中心模块 ===")
my_reports = test("我的报告", "GET", f"{BASE}/reports/my-reports", 200, token=token)
if my_reports:
    print(f"     报告数: {len(my_reports)}")

test("审核列表", "GET", f"{BASE}/reports/review-list", 200, token=token)

# 获取模板列表
test("模板列表", "GET", f"{BASE}/reports/custom-templates", 200, token=token)

# 创建自定义模板
test("创建自定义模板", "POST", f"{BASE}/reports/custom-templates", 200, {
    "name": "测试模板",
    "description": "用于测试",
    "sections": ["概述", "数据分析", "结论"],
    "scenario": "绿色信贷"
}, token=token)

# ========================
# 4. 驾驶舱模块
# ========================
print("\n=== 驾驶舱模块 ===")
monitor = test("碳排放监控", "GET", f"{BASE}/dashboard/emission-monitor", 200, token=token)
if monitor:
    print(f"     标题: {monitor.get('title')}, 数据点数: {len(monitor.get('data', []))}")

test("能耗结构", "GET", f"{BASE}/dashboard/energy-structure", 200, token=token)
test("ESG看板", "GET", f"{BASE}/dashboard/esg-board", 200, token=token)
test("关键指标", "GET", f"{BASE}/dashboard/key-indicators", 200, token=token)

# ========================
# 5. 金融对接模块
# ========================
print("\n=== 金融对接模块 ===")
recs = test("产品推荐", "GET", f"{BASE}/finance/recommendations", 200, token=token)
if recs:
    products = recs.get("products", [])
    print(f"     产品数: {len(products)}")
    for p in products[:3]:
        print(f"     - {p.get('name')}: 匹配度{p.get('match_score')}%")

test("融资方案对比", "GET", f"{BASE}/finance/comparison", 200, token=token)

# 获取申请材料
mats = test("申请材料列表", "GET", f"{BASE}/finance/materials", 200, token=token)
if mats:
    print(f"     材料数: {len(mats)}")

# 上传材料
test("上传材料", "POST", f"{BASE}/finance/materials", 200, {
    "file_name": "ESG报告.pdf",
    "file_type": "pdf",
    "doc_category": "esg"
}, token=token)

# 批量申请
batch_res = test("批量申请", "POST", f"{BASE}/finance/batch-apply", 200, {
    "product_ids": [1, 2],
    "purpose": "申请绿色信贷"
}, token=token)

# 进度跟踪（用批量申请创建了记录）
apps = requests.get(f"{BASE}/finance/applications", headers={"Authorization": f"Bearer {token}"}).json()
if apps:
    app_id = apps[0]["id"]
    test("进度跟踪", "GET", f"{BASE}/finance/progress/{app_id}", 200, token=token)
else:
    test("进度跟踪(先申请)", "POST", f"{BASE}/finance/apply", 200, {
        "product_id": 1, "amount": 500000, "purpose": "测试"
    }, token=token)

# ========================
# 结果汇总
# ========================
print(f"\n{'='*50}")
print(f"测试完成: ✅ {passed} 通过, ❌ {failed} 失败")
print(f"{'='*50}")
sys.exit(0 if failed == 0 else 1)
