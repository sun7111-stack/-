with open('demo-flow.js', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(r"\.innerHTML = DemoState", ".innerHTML = DemoState")
text = text.replace(r".innerHTML = `经平台", "summary: `经平台")

with open('demo-flow.js', 'w', encoding='utf-8') as f:
    f.write(text)
