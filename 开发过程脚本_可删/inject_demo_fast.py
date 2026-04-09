with open("demo-flow.js", "r", encoding="utf-8") as f:
    content = f.read()

if "updateTwinEmissions" not in content:
    target = "function renderBenchmarkChart(currentValue) {"
    replacement = "function renderBenchmarkChart(currentValue) {\n    if (window.updateTwinEmissions) window.updateTwinEmissions(currentValue || 10.5);"
    if target in content:
        content = content.replace(target, replacement)
        with open("demo-flow.js", "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated demo-flow.js!")
    else:
        print("Target not found...")
else:
    print("Already updated!")
