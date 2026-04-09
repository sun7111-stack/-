import re

with open("demo-flow.js", "r", encoding="utf-8") as f:
    content = f.read()

# 在 carbon-calc 成功后添加触发数字孪生更新的代码
search_pattern = r"(// 4\. 显示左上：核算模型\n\s+document\.getElementById\('benchmarkCompareBox'\)\.style\.display = 'block';)"
replace_pattern = r"\1\n\n            // --- 触发数字孪生效果更新 ---\n            if (window.updateTwinEmissions) {\n                window.updateTwinEmissions(res.total_carbon_tons || 10.5);\n            }"

if re.search(search_pattern, content):
    content = re.sub(search_pattern, replace_pattern, content)
    with open("demo-flow.js", "w", encoding="utf-8") as f:
        f.write(content)
    print("已成功修改 demo-flow.js，注入数字孪生联动")
else:
    print("未找到对应的锚点")
