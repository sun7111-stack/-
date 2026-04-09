with open("twin3d.js", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace('mesh.material.emissive.setHex', 'if(mesh.material.emissive) mesh.material.emissive.setHex')
text = text.replace('mesh.material.color.setHex', 'if(mesh.material.color) mesh.material.color.setHex')

with open("twin3d.js", "w", encoding="utf-8") as f:
    f.write(text)

print("Fixed TypeError on emissive/color.setHex")
