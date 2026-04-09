import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add html2pdf.js before echarts.min.js scripts
script_insert = '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>\n    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>'
html = html.replace('<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>', script_insert)

# 2. Add Export Button inside reportResultBox
btn_insert = '''<p id="financeSuggestionText" class="text-dark fw-bold p-3 bg-info bg-opacity-10 rounded border border-info"></p>
                                  
                                  <div class="text-center mt-5 mb-2" id="exportBtnContainer">
                                      <button id="exportPdfBtn" class="btn btn-danger btn-lg px-4 rounded-pill shadow-sm"><i class="fas fa-file-pdf me-2"></i>一键导出红头报告(PDF)</button>
                                  </div>'''
html = html.replace('<p id="financeSuggestionText" class="text-dark fw-bold p-3 bg-info bg-opacity-10 rounded border border-info"></p>', btn_insert)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)


# Now update demo-flow.js
with open('demo-flow.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

# Add bindExportPdfButton to initDemoFlow
js_content = js_content.replace('bindReportButton();', 'bindReportButton();\n    bindExportPdfButton();')

# Define bindExportPdfButton
pdf_logic = """
function bindExportPdfButton() {
    const btn = document.getElementById('exportPdfBtn');
    if (!btn) return;

    btn.addEventListener('click', async () => {
        const reportElement = document.getElementById('reportResultBox');
        if (!reportElement) return;

        // Hide the button itself before generating PDF
        const btnContainer = document.getElementById('exportBtnContainer');
        if(btnContainer) btnContainer.style.display = 'none';
        
        if(typeof showToast === 'function') showToast('正在渲染企业级电子红头报告，请稍候...', 'info');

        try {
            // Setup a temporary header to look like a real document
            const originalBody = reportElement.innerHTML;
            const docHeader = `
                <div style="text-align:center; color: red; margin-bottom: 20px;">
                    <h1 style="font-size: 32px; font-weight: bold; border-bottom: 3px solid red; padding-bottom: 10px; margin-bottom: 20px;">★ 碳融智核大模型评估报告 ★</h1>
                    <p style="color: black; text-align: right;">编号：CRZH-${new Date().getFullYear()}${String(new Date().getMonth()+1).padStart(2,'0')}${String(new Date().getDate()).padStart(2,'0')}-${Math.floor(Math.random() * 9000 + 1000)}</p>
                </div>
            `;
            
            reportElement.style.padding = '40px 20px';
            reportElement.style.backgroundColor = '#fff';
            reportElement.innerHTML = docHeader + originalBody;

            const opt = {
                margin:       10,
                filename:     `碳中和与ESG诊断红头报告_${new Date().toLocaleDateString().replace(/\//g, '-')}.pdf`,
                image:        { type: 'jpeg', quality: 0.98 },
                html2canvas:  { scale: 2, useCORS: true },
                jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
            };
            
            await html2pdf().set(opt).from(reportElement).save();
            
            if(typeof showToast === 'function') showToast('PDF 下载成功！', 'success');
            
            // Restore original DOM
            reportElement.innerHTML = originalBody;
            reportElement.style.padding = '';
            reportElement.style.backgroundColor = '';
        } catch(e) {
            console.error('PDF生成失败:', e);
            alert('PDF 生成失败，请检查浏览器权限。');
        } finally {
            if(btnContainer) btnContainer.style.display = 'block';
        }
    });
}
"""

js_content = js_content + "\n" + pdf_logic

with open('demo-flow.js', 'w', encoding='utf-8') as f:
    f.write(js_content)
