with open("demo-flow.js", "r", encoding="utf-8") as f:
    content = f.read()

import re

def fix(match):
    return match.group(0) + "\n        if (window.updateTwinEmissions) window.updateTwinEmissions(res.total_carbon_tons || currentValue || 10.5);"

# Let's put it back inside renderBenchmarkChart
target_func = "function renderBenchmarkChart(currentValue) {"
if target_func in content and "updateTwinEmissions" not in content:
    content = content.replace(target_func, target_func + "\n      if (window.updateTwinEmissions) window.updateTwinEmissions(currentValue || 10.5);")

with open("demo-flow.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Simplified twin update into chart method!")
