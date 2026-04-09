import re
with open('demo-flow.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the OCR Success banner
old_ocr = """            <p class="mb-2"><i class="fas fa-tag me-2"></i><strong>单据类型:</strong> ${DemoState.ocrResult.type}</p>
            <p class="mb-2"><i class="fas fa-bolt me-2"></i><strong>提取用量:</strong> <span class="fs-4 fw-bold">${DemoState.ocrResult.usage}</span> ${DemoState.ocrResult.unit}</p>
            <p class="mb-0"><i class="fas fa-calendar-alt me-2"></i><strong>单据日期:</strong> ${DemoState.ocrResult.date}</p>"""

new_ocr = """            <p class="mb-2"><i class="fas fa-tag me-2"></i><strong>单据类型:</strong> ${DemoState.ocrResult.type} <span class="badge bg-info text-dark ms-2">AI真实识别</span></p>
            <p class="mb-2"><i class="fas fa-bolt me-2"></i><strong>提取用量:</strong> <span class="fs-4 fw-bold">${DemoState.ocrResult.usage}</span> ${DemoState.ocrResult.unit}</p>
            <p class="mb-0"><i class="fas fa-calendar-alt me-2"></i><strong>单据日期:</strong> ${DemoState.ocrResult.date}</p>"""

content = content.replace(old_ocr, new_ocr)

with open('demo-flow.js', 'w', encoding='utf-8') as f:
    f.write(content)
