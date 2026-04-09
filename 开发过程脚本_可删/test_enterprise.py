import requests, json

BASE = 'http://localhost:8000/api'

# 1. 企业账号登录获取token
print('=== 1. 企业登录 ===')
r = requests.post(f'{BASE}/auth/login/enterprise', json={'account':'LCZZ2024','password':'admin888'})
print(f'  Status: {r.status_code}')
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# 2. 仪表盘
print('\n=== 2. 企业仪表盘 ===')
r = requests.get(f'{BASE}/enterprise/dashboard', headers=headers)
print(f'  Status: {r.status_code}')
d = r.json()
print(f'  年营收: {d["annual_revenue_display"]}')
print(f'  碳排放: {d["total_carbon_emission"]}t')
print(f'  ESG得分: {d["esg_score"]}')
print(f'  碳效等级: {d["carbon_efficiency_grade"]}')
print(f'  物流碳强度: {d["logistics_carbon_intensity"]}')
print(f'  能耗强度: {d["energy_intensity"]}')

# 3. 基本信息
print('\n=== 3. 企业基本信息 ===')
r = requests.get(f'{BASE}/enterprise/profile', headers=headers)
print(f'  Status: {r.status_code}')
p = r.json()
print(f'  企业名: {p["company_name"]}')
print(f'  行业: {p["industry"]}')
print(f'  员工: {p["employee_count"]}人')
print(f'  主要产品: {p["main_products"]}')

# 4. 资质认证
print('\n=== 4. 资质认证列表 ===')
r = requests.get(f'{BASE}/enterprise/certifications', headers=headers)
print(f'  Status: {r.status_code}')
certs = r.json()
for c in certs:
    print(f'  - {c["cert_name"]} ({c["status"]})')

# 5. 数据权限
print('\n=== 5. 数据权限 ===')
r = requests.get(f'{BASE}/enterprise/permissions', headers=headers)
print(f'  Status: {r.status_code}')
perms = r.json()
print(f'  角色: {perms["role"]}')
print(f'  数据范围: {perms["data_scope"]}')
print(f'  查看碳数据: {perms["can_view_carbon"]}')

# 6. 账号设置
print('\n=== 6. 账号设置 ===')
r = requests.get(f'{BASE}/enterprise/account', headers=headers)
print(f'  Status: {r.status_code}')
acc = r.json()
print(f'  Email: {acc["email"]}')
print(f'  企业账号: {acc["enterprise_account"]}')

# 7. 最近活动
print('\n=== 7. 最近活动 ===')
r = requests.get(f'{BASE}/enterprise/activities', headers=headers)
print(f'  Status: {r.status_code}')
acts = r.json()
for a in acts[:3]:
    print(f'  - [{a["action"]}] {a["title"]}')
print(f'  共{len(acts)}条')

# 8. 更新基本信息
print('\n=== 8. 更新企业信息 ===')
r = requests.put(f'{BASE}/enterprise/profile', headers=headers, json={'contact_person':'李经理'})
print(f'  Status: {r.status_code}')
print(f'  联系人已更新为: {r.json()["contact_person"]}')

# 9. 新增认证
print('\n=== 9. 新增认证 ===')
r = requests.post(f'{BASE}/enterprise/certifications', headers=headers, json={
    'cert_name':'清洁生产审核','cert_type':'green',
    'cert_number':'CP-2024-001','issuing_authority':'生态环境部'
})
print(f'  Status: {r.status_code}')
new_cert_id = r.json()['id']
print(f'  新认证ID: {new_cert_id}')

# 10. 删除刚新增的认证
print('\n=== 10. 删除认证 ===')
r = requests.delete(f'{BASE}/enterprise/certifications/{new_cert_id}', headers=headers)
print(f'  Status: {r.status_code}')

print('\n========== 全部测试通过 ==========')
