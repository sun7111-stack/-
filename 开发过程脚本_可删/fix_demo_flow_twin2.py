import re

with open("demo-flow.js", "r", encoding="utf-8") as f:
    content = f.read()

# Fallback 中也加入数字孪生联动
search_pattern2 = r"(document\.getElementById\('benchmarkCompareBox'\)\.style\.display = 'block';)"

# 简单替换全部
if "window.updateTwinEmissions" not in content:
    content = content.replace(
        "document.getElementById('benchmarkCompareBox').style.display = 'block';",
        "document.getElementById('benchmarkCompareBox').style.display = 'block';\n            if (window.updateTwinEmissions) window.updateTwinEmissions(10.5);"
    )
    with open("demo-flow.js", "w", encoding="utf-8") as f:
        f.write(content)
    print("已成功修改 demo-flow.js 全部位置")
else:
    print("已存在联动代码")
