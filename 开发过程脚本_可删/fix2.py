import re

with open('demo-flow.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix everything!
# Basically look for: = \n        <div class="alert
text = re.sub(
    r"\.innerHTML =\s*<div class=\"alert alert-warning mb-0 border-0\">\s*<p class=\"mb-2\"><i class=\"fas fa-tag me-2\"></i><strong>单据类型:</strong> </p>\s*<p class=\"mb-2\"><i class=\"fas fa-bolt me-2\"></i><strong>提取用量:</strong> <span class=\"fs-4 fw-bold\"></span> </p>\s*<p class=\"mb-0\"><i class=\"fas fa-calendar-alt me-2\"></i><strong>单据日期:</strong> </p>\s*</div>\s*;",
    r"""\.innerHTML = `
        <div class="alert alert-warning mb-0 border-0">
            <p class="mb-2"><i class="fas fa-tag me-2"></i><strong>单据类型:</strong> ${DemoState.ocrResult.type}</p>
            <p class="mb-2"><i class="fas fa-bolt me-2"></i><strong>提取用量:</strong> <span class="fs-4 fw-bold">${DemoState.ocrResult.usage}</span> ${DemoState.ocrResult.unit}</p>
            <p class="mb-0"><i class="fas fa-calendar-alt me-2"></i><strong>单据日期:</strong> ${DemoState.ocrResult.date}</p>
        </div>
    `;""", text)

text = re.sub(
    r"\.innerHTML =\s*<li class=\"list-group-item d-flex justify-content-between align-items-center py-3\">\s*<div><i class=\"fas fa-plug text-primary me-2\"></i>外购电力隐含碳排 \(演示数据\)</div>\s*<span class=\"badge bg-warning text-dark rounded-pill fs-6\"> tCO₂e</span>\s*</li>\s*;",
    r"""\.innerHTML = `
        <li class="list-group-item d-flex justify-content-between align-items-center py-3">
            <div><i class="fas fa-plug text-primary me-2"></i>外购电力隐含碳排 (演示数据)</div>
            <span class="badge bg-warning text-dark rounded-pill fs-6">${total} tCO₂e</span>
        </li>
    `;""", text)

text = re.sub(
    r"\.innerHTML = DemoState.riskResult.details\s*\.map\(item => <p class=\"text-warning fw-bold mb-2 darken-text\"><i class=\"fas fa-check-circle me-2\"></i></p>\)\s*\.join\(''\);",
    r"""\.innerHTML = DemoState.riskResult.details
        .map(item => `<p class="text-warning fw-bold mb-2 darken-text"><i class="fas fa-check-circle me-2"></i>${item}</p>`)
        .join('');""", text)

text = re.sub(
    r"summary: `?经平台核算，贵司本期总碳排放为 <strong>[^<]*</strong>，数据已通过区块链存证验真。\(由于超时转本地演示\)`?,",
    r"""summary: `经平台核算，贵司本期总碳排放为 <strong>${DemoState.carbonResult && DemoState.carbonResult.total_emissions ? DemoState.carbonResult.total_emissions : 7.26} 吨</strong>，数据已通过区块链存证验真。(由于超时转本地演示)`, """, text)

with open('demo-flow.js', 'w', encoding='utf-8') as f:
    f.write(text)
