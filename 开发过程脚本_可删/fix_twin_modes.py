import re

with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

# 替换按钮添加 ID
content = content.replace(
    '<button class="btn btn-sm btn-outline-info active text-white border-info me-2"',
    '<button id="twinTotalBtn" class="btn btn-sm btn-outline-info active text-white border-info me-2"'
)
content = content.replace(
    '<button class="btn btn-sm btn-outline-danger text-white border-secondary me-2"',
    '<button id="twinRiskBtn" class="btn btn-sm btn-outline-danger text-white border-secondary me-2"'
)
content = content.replace(
    '<button class="btn btn-sm btn-outline-success text-white border-secondary"',
    '<button id="twinEsgBtn" class="btn btn-sm btn-outline-success text-white border-secondary"'
)

# 替换文字区添加 ID
if 'id="twinExplanation"' not in content:
    content = content.replace(
        '<div class="text-light small text-end" style="font-size: 12px; font-family: sans-serif;">',
        '<div id="twinExplanation" class="text-light small text-end" style="font-size: 12px; font-family: sans-serif;">'
    )

with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated index.html to add IDs.")

with open("twin3d.js", "r", encoding="utf-8") as f:
    js_content = f.read()

if "function switchTwinMode" not in js_content:
    append_js = """

// --- 模式切换逻辑 ---
let currentTwinMode = 'total';
let originalMaterials = new Map();

function switchTwinMode(mode) {
    if (mode === currentTwinMode) return;
    currentTwinMode = mode;
    
    const expDom = document.getElementById('twinExplanation');
    const b1 = document.getElementById('twinTotalBtn');
    const b2 = document.getElementById('twinRiskBtn');
    const b3 = document.getElementById('twinEsgBtn');
    
    // Reset buttons
    [b1, b2, b3].forEach(b => {
        if(b){
            b.classList.remove('active', 'border-info', 'border-danger', 'border-success');
            b.classList.add('border-secondary');
        }
    });

    if (mode === 'total') {
        if(b1) { b1.classList.add('active', 'border-info'); b1.classList.remove('border-secondary'); }
        if(expDom) expDom.innerHTML = '<i class="fas fa-info-circle text-info me-1"></i> 当前监测结果显示，核心排放节点主要集中于高负载电力设备区域，建议优先关注用电结构优化。';
        
        // 恢复原有材质颜色
        factoryGroup.children.forEach(mesh => {
            if (originalMaterials.has(mesh.uuid)) {
                mesh.material.color.setHex(originalMaterials.get(mesh.uuid));
                mesh.material.emissive.setHex(0x000000);
            }
        });
        document.getElementById('twinEmissionsRate').parentElement.parentElement.innerHTML = `
            <p class="mb-1 text-info"><i class="fas fa-satellite-dish me-2"></i>实时传感采集点位(IOT)</p>
            <p class="mb-1">STATUS: <span class="text-success flash-status">ONLINE 联机</span></p>
            <p class="mb-1">RATE: <span id="twinEmissionsRate" class="text-warning fw-bold fs-5">0.82</span> <span class="text-muted">kgCO₂/sec</span></p>
            <p class="mb-0">TEMP: <span class="text-danger">85.4°C</span> | LOAD: <span class="text-primary">92%</span></p>
        `;
    } 
    else if (mode === 'risk') {
        if(b2) { b2.classList.add('active', 'border-danger'); b2.classList.remove('border-secondary'); }
        if(expDom) expDom.innerHTML = '<i class="fas fa-exclamation-triangle text-danger me-1"></i> 告警：锅炉与发电机组区域温度异常，存在较高的能耗与碳排外泄风险。';
        
        // 记录原有材质，给建筑发红光
        factoryGroup.children.forEach(mesh => {
            if (!originalMaterials.has(mesh.uuid) && mesh.material.color) {
                originalMaterials.set(mesh.uuid, mesh.material.color.getHex());
            }
            // 不要改霓虹灯等自发光的原本特性
            if(mesh.geometry.type === 'BoxGeometry' && mesh.position.y < 5) {
                mesh.material.color.setHex(0xff3333);
                mesh.material.emissive.setHex(0x440000); // 红光发热
            }
        });
    }
    else if (mode === 'esg') {
        if(b3) { b3.classList.add('active', 'border-success'); b3.classList.remove('border-secondary'); }
        if(expDom) expDom.innerHTML = '<i class="fas fa-leaf text-success me-1"></i> 设备均已接入绿电网络，S(社会)无安全事故，G(治理)数据实时上链防篡改。';
        
        // 恢复原有材质颜色，发绿光
        factoryGroup.children.forEach(mesh => {
            if (originalMaterials.has(mesh.uuid)) {
                mesh.material.color.setHex(0x225522);
                mesh.material.emissive.setHex(0x002200);
            }
        });
        
        // 切换左上角文字框为 E/S/G 指标
        const sensorBox = document.querySelector('.twin-sensor');
        if(sensorBox) {
            sensorBox.innerHTML = `
                <p class="mb-1 text-success"><i class="fas fa-chart-pie me-2"></i>ESG 即时指标面板</p>
                <p class="mb-1">E (环境): 绿电覆盖率 <span class="text-success fw-bold">45%</span></p>
                <p class="mb-1">S (社会): 安全生产天数 <span class="text-info fw-bold">124</span></p>
                <p class="mb-0">G (治理): 数据上链状态 <span class="text-warning flash-status">区块写入中</span></p>
            `;
        }
    }
}

// 绑定事件到 DOM
document.addEventListener('DOMContentLoaded', () => {
    // 监听按键
    // 我们需要在页面能够捕捉到这两个按键
    const checkBtnReady = setInterval(() => {
        const b1 = document.getElementById('twinTotalBtn');
        const b2 = document.getElementById('twinRiskBtn');
        const b3 = document.getElementById('twinEsgBtn');
        if (b1 && b2 && b3) {
            b1.addEventListener('click', () => switchTwinMode('total'));
            b2.addEventListener('click', () => switchTwinMode('risk'));
            b3.addEventListener('click', () => switchTwinMode('esg'));
            clearInterval(checkBtnReady);
        }
    }, 500);
});
"""
    with open("twin3d.js", "a", encoding="utf-8") as f:
        f.write(append_js)
    print("Updated twin3d.js to add mode switching logic.")
else:
    print("Mode switching logic already in twin3d.js.")
