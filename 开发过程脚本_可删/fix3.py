with open('demo-flow.js', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(r"\.innerHTML = `", ".innerHTML = `")

with open('demo-flow.js', 'w', encoding='utf-8') as f:
    f.write(text)
