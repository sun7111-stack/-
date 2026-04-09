with open("twin3d.js", "r", encoding="utf-8") as f:
    text = f.read()

# Replace the beginning of switchTwinMode
if "function switchTwinMode(mode) {" in text:
    text = text.replace(
        "function switchTwinMode(mode) {",
        "function switchTwinMode(mode) {\n    try {\n        console.log('Switching to mode:', mode);"
    )
    # The end of the function is hard to locate accurately with regex, let's just replace the last bracket manually
    text = text.replace(
        """// 绑定事件到 DOM""",
        """} catch (e) {
        console.error('Error switching mode:', e);
    }
}

// 绑定事件到 DOM"""
    )

with open("twin3d.js", "w", encoding="utf-8") as f:
    f.write(text)

print("Wrapped switchTwinMode in try-catch")
