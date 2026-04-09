with open("style.css", "r", encoding="utf-8") as f:
    content = f.read()

if "factory3dContainer" not in content:
    content += """
/* 3D Êý×ÖÂÏÉúÈÝÆ÷ */
#factory3dContainer {
    width: 100%;
    height: 300px;
    background: #02040a;
    border-radius: 8px;
    position: relative;
    overflow: hidden;
    box-shadow: inset 0 0 20px rgba(13, 202, 240, 0.2);
}

.twin-sensor {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(13, 202, 240, 0.5);
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 0.85rem;
    color: #0dcaf0;
    backdrop-filter: blur(2px);
}
"""
    with open("style.css", "w", encoding="utf-8") as f:
        f.write(content)
print("Style CSS Check done")
