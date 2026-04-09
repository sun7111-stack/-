with open("twin3d.js", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("function switchTwinMode(mode) {\n    try {\n        console.log('Switching to mode:', mode);", "function switchTwinMode(mode) {\n        console.log('Switching to mode:', mode);")

text = text.replace("} catch (e) {\n        console.error('Error switching mode:', e);\n    }\n}\n\n// 绑定事件到 DOM", "// 绑定事件到 DOM")

with open("twin3d.js", "w", encoding="utf-8") as f:
    f.write(text)

print("Removed syntax error")
