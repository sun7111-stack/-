import re

with open("index.html", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace('id="twinTotalBtn"', 'id="twinTotalBtn" onclick="switchTwinMode(\'total\')"')
text = text.replace('id="twinRiskBtn"', 'id="twinRiskBtn" onclick="switchTwinMode(\'risk\')"')
text = text.replace('id="twinEsgBtn"', 'id="twinEsgBtn" onclick="switchTwinMode(\'esg\')"')

with open("index.html", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated inline onclick attributes.")
