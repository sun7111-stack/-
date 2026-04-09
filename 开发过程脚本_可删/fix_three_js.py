with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

if "https://cdn.jsdelivr.net/npm/three@0.135.0/build/three.min.js" not in content:
    content = content.replace("</head>", '    <script src="https://cdn.jsdelivr.net/npm/three@0.135.0/build/three.min.js"></script>\n    <script src="https://cdn.jsdelivr.net/npm/three@0.135.0/examples/js/controls/OrbitControls.js"></script>\n</head>')
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)

print("ThreeJS Check done")
