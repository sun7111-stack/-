with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

if "init3DTwin" not in content:
    content = content.replace("</body>", "  <script>\n    if (typeof init3DTwin === 'function') setTimeout(init3DTwin, 500);\n  </script>\n</body>")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)
print("Finished adding init3DTwin call")
