with open("demo-flow.js", "r", encoding="utf-8") as f:
    content = f.read()

target = "setTimeout(() => {\n            document.getElementById('benchmarkCompareBox').style.display = 'block';\n            renderBenchmarkChart(48.5);"
replacement = "setTimeout(() => {\n            document.getElementById('benchmarkCompareBox').style.display = 'block';\n            renderBenchmarkChart(48.5);\n            if (window.updateTwinEmissions) window.updateTwinEmissions(48.5);"
content = content.replace(target, replacement)

target2 = "renderBenchmarkChart(res.total_carbon_tons || 10.5);\n        if (window.updateTwinEmissions) window.updateTwinEmissions(res.total_carbon_tons || 10.5);"
replacement2 = "renderBenchmarkChart(res.total_carbon_tons || 10.5);"
content = content.replace(target2, replacement2)

with open("demo-flow.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated mock and real paths!")
