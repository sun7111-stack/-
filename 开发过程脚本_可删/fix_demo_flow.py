import re

with open("demo-flow.js", "r", encoding="utf-8") as f:
    text = f.read()

# remove all existing window.updateTwinEmissions calls to clean it up
text = re.sub(r'^\s*if\s*\(window\.updateTwinEmissions\)[^\n]+$', '', text, flags=re.MULTILINE)

# insert it explicitly inside renderBenchmarkChart
target_func = "function renderBenchmarkChart(currentValue) {"
rep_func = target_func + "\n      if (window.updateTwinEmissions) window.updateTwinEmissions(currentValue || 10.5);"

if target_func in text:
    text = text.replace(target_func, rep_func)

with open("demo-flow.js", "w", encoding="utf-8") as f:
    f.write(text)
print("demo-flow.js twin bug fixed")
