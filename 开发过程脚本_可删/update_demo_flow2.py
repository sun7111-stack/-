with open("demo-flow.js", "r", encoding="utf-8") as f:
    content = f.read()

count = 0

import re
# Remove all old ones
content = re.sub(r"\s*if\s*\(window\.updateTwinEmissions\)\s*window\.updateTwinEmissions\([^)]+\);", "", content)

# Add it neatly right where the carbonResultBox is displayed
search_str = "document.getElementById('carbonResultBox').style.display = 'flex';"
rep_str = "document.getElementById('carbonResultBox').style.display = 'flex';\n        if (window.updateTwinEmissions) window.updateTwinEmissions(res.total_carbon_tons || 10.5);"

if search_str in content:
    content = content.replace(search_str, rep_str)

search_str2 = "document.getElementById('carbonResultBox').style.display = 'flex'; // Use flex for row"
rep_str2 = "document.getElementById('carbonResultBox').style.display = 'flex'; // Use flex for row\n            if (window.updateTwinEmissions) window.updateTwinEmissions(48.5);"

if search_str2 in content:
    content = content.replace(search_str2, rep_str2)

with open("demo-flow.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Simplified twin update!")
