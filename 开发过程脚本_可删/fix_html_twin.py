with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

# 在 body 之前调用 init3DTwin
if "init3DTwin();" not in content:
    content = content.replace("</body>", "  <script>\n    // 启动 3D 孪生\n    if (typeof init3DTwin === 'function') {\n      setTimeout(init3DTwin, 500);\n    }\n  </script>\n</body>")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)
print("已修改 index.html 启动代码")
