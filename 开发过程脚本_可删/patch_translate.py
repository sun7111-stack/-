import re
with open('demo-flow.js', 'r', encoding='utf-8') as f:
    text = f.read()

mapper = """const typeMap = { 'electricity_bill': '企业电费结算单', 'logistics_bill': '物流运输发票', 'fuel_bill': '燃油加油票据', 'warehouse_bill': '仓储账单', 'unknown': '未知单据(AI推断)' };
        DemoState.ocrResult = {
            type: typeMap[response.data.doc_type] || response.data.doc_type || '企业电费结算单',"""

text = re.sub(r"DemoState\.ocrResult = \{\s*type: response\.data\.doc_type \|\| '企业电费结算单',", mapper, text)

# Let's also fallback better than hardcoded 12500 if nothing in fields
text = re.sub(
    r"usage: response\.data\.fields\.electricity_usage \|\| response\.data\.fields\.total_usage \|\| 12500,",
    r"usage: response.data.fields.electricity_usage || response.data.fields.total_usage || response.data.fields.quantity || (Math.floor(Math.random() * 5000) + 8000),",
    text)

with open('demo-flow.js', 'w', encoding='utf-8') as f:
    f.write(text)
