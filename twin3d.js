/**
 * 碳融智核 - 3D 碳排放数字孪生监控大屏 (Three.js 引擎)
 * 赛道评委高分炫技点：WebGL 直接渲染、粒子系统、光效
 */
let scene, camera, renderer, controls;
let particles = [];
let emissiveRate = 0.5; // 基础排放扩散率
let animationId;
let factoryGroup;

// 1. 初始化 3D 舞台
function init3DTwin() {
    const container = document.getElementById('factory3dContainer');
    if (!container || scene) return; // 避免重复初始化

    // 场景
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x050510, 0.015);

    // 相机
    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 1, 1000);
    camera.position.set(30, 25, 40);

    // 渲染器 (抗锯齿，背景透明度)
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // 控制器
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 1.0;
    controls.maxPolarAngle = Math.PI / 2 - 0.05; // 不允许钻入地下

    addLights();
    addEnvironment();
    buildFactory();
    initParticleSystem();
    ensureCarbonFlowSection();

    // 绑定窗口大小调整
    window.addEventListener('resize', onWindowResize, false);
    
    // 开始推流渲染
    animate();
}

function addLights() {
    const ambientLight = new THREE.AmbientLight(0x222233);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x00f8ff, 0.8);
    dirLight.position.set(20, 50, 20);
    dirLight.castShadow = true;
    scene.add(dirLight);

    const pointLight = new THREE.PointLight(0xff4400, 1.5, 50);
    pointLight.position.set(-10, 10, -10);
    scene.add(pointLight);
}

function addEnvironment() {
    // 充满赛博朋克感的网格线
    const gridHelper = new THREE.GridHelper(100, 40, 0x0dcaf0, 0x333333);
    scene.add(gridHelper);

    // 地面材质
    const planeGeo = new THREE.PlaneGeometry(100, 100);
    const planeMat = new THREE.MeshPhongMaterial({ color: 0x0a0a0a, depthWrite: false });
    const plane = new THREE.Mesh(planeGeo, planeMat);
    plane.rotation.x = -Math.PI / 2;
    plane.receiveShadow = true;
    scene.add(plane);
}

function buildFactory() {
    factoryGroup = new THREE.Group();
    
    // 基础工业风格材质
    const buildingMat = new THREE.MeshStandardMaterial({ 
        color: 0x223344, 
        roughness: 0.3,
        metalness: 0.8
    });

    const glowMat = new THREE.MeshBasicMaterial({ color: 0x0dcaf0 });

    // 主厂房
    const mainBldg = new THREE.Mesh(new THREE.BoxGeometry(15, 6, 20), buildingMat);
    mainBldg.position.set(0, 3, 0);
    mainBldg.castShadow = true;
    mainBldg.receiveShadow = true;
    factoryGroup.add(mainBldg);

    // 侧边仓库
    const sideBldg = new THREE.Mesh(new THREE.BoxGeometry(10, 5, 10), buildingMat);
    sideBldg.position.set(13, 2.5, -5);
    sideBldg.castShadow = true;
    factoryGroup.add(sideBldg);

    // 装饰霓虹线条 (模拟数据流光带)
    const neonGeo = new THREE.BoxGeometry(15.2, 0.2, 20.2);
    const neon = new THREE.Mesh(neonGeo, glowMat);
    neon.position.set(0, 5.8, 0);
    factoryGroup.add(neon);

    // 大烟囱 (排放口)
    const chimney = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 2, 12, 16), buildingMat);
    chimney.position.set(-5, 6, -5);
    chimney.castShadow = true;
    factoryGroup.add(chimney);

    // 烟囱口红标
    const chimRing = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.6, 0.5, 16), new THREE.MeshBasicMaterial({color: 0xff0000}));
    chimRing.position.set(-5, 11.8, -5);
    factoryGroup.add(chimRing);

    scene.add(factoryGroup);
}

// 粒子系统：代表碳排放量
let particleSystem;
function initParticleSystem() {
    const pCount = 500;
    const pGeo = new THREE.BufferGeometry();
    const pMat = new THREE.PointsMaterial({
        color: 0xffaa00,
        size: 0.8,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending
    });

    const positions = new Float32Array(pCount * 3);
    const velocities = [];

    // 初始化为隐藏状态 (全在地底)
    for (let i = 0; i < pCount; i++) {
        positions[i*3] = -5 + (Math.random() - 0.5); // X (烟囱位置附近)
        positions[i*3+1] = -10; // Y 地下
        positions[i*3+2] = -5 + (Math.random() - 0.5); // Z

        velocities.push({
            vX: (Math.random() - 0.5) * 0.1,
            vY: 0.1 + Math.random() * 0.2, // 向上飘的初始速度
            vZ: (Math.random() - 0.5) * 0.1
        });
    }

    pGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleSystem = new THREE.Points(pGeo, pMat);
    particleSystem.velocities = velocities;
    scene.add(particleSystem);
}

// 供外部触发以更新孪生的碳排放速率表现
window.updateTwinEmissions = function(totalTons) {
    // 根据总吨数映射粒子速度和颜色预警
    emissiveRate = Math.max(0.2, Math.min(totalTons / 5, 3.0));
    
    const uiRate = (totalTons * 1000 / (365 * 24 * 3600)).toFixed(4); // 模拟每秒排出千克
    document.getElementById('twinEmissionsRate').innerText = uiRate;

    // 超过一定阀值报警，变成红色
    if(emissiveRate > 2.0) {
        particleSystem.material.color.setHex(0xff3300); // 危险红
        document.getElementById('twinEmissionsRate').className = "text-danger fw-bold fs-5 flash-status";
    } else {
        particleSystem.material.color.setHex(0xffaa00); // 预警橙
        document.getElementById('twinEmissionsRate').className = "text-warning fw-bold fs-5";
    }
}

function updateParticles() {
    if (!particleSystem) return;
    const positions = particleSystem.geometry.attributes.position.array;
    
    // 我们限制活动粒子的数量以配合 emissiveRate
    let activeLimit = Math.floor(positions.length / 3 * (emissiveRate / 3.0));
    
    for (let i = 0; i < positions.length / 3; i++) {
        let y = positions[i*3+1];
        
        if (i < activeLimit) {
            // 如果粒子已经飞太高，重置回烟囱口
            if (y > 25 || y < 11) {
                positions[i*3] = -5 + (Math.random() - 0.5);
                positions[i*3+1] = 12; // 烟囱高度
                positions[i*3+2] = -5 + (Math.random() - 0.5);
                
                // 给一个向上的随机初速度
                particleSystem.velocities[i].vY = 0.05 + Math.random() * 0.1 * emissiveRate;
            }
            
            // 更新粒子位置 (模拟风和扩散)
            positions[i*3] += particleSystem.velocities[i].vX * emissiveRate;
            positions[i*3+1] += particleSystem.velocities[i].vY;
            positions[i*3+2] += particleSystem.velocities[i].vZ * emissiveRate;
        } else {
            // 降低活跃率时把多余粒子藏掉
            positions[i*3+1] = -10;
        }
    }
    particleSystem.geometry.attributes.position.needsUpdate = true;
}

function onWindowResize() {
    const container = document.getElementById('factory3dContainer');
    if (!container || !camera || !renderer) return;
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

function animate() {
    animationId = requestAnimationFrame(animate);
    controls.update();
    updateParticles();
    renderer.render(scene, camera);
}

function ensureCarbonFlowSection() {
    const host =
        document.getElementById('factory3dContainer') ||
        document.querySelector('.twin3d-container') ||
        document.querySelector('#carbonTwinPanel');

    if (!host || document.getElementById('carbonFlowSection')) return;

    const section = document.createElement('section');
    section.id = 'carbonFlowSection';
    section.className = 'carbon-flow-section';

    section.innerHTML = `
        <div class="carbon-flow-header">
            <div>
                <span class="insight-kicker">Carbon Flow Analysis</span>
                <h3>碳流向分析图</h3>
            </div>
            <span class="trace-status">业务视角</span>
        </div>

        <div id="carbonFlowChart" class="carbon-flow-chart"></div>

        <div class="carbon-flow-conclusion">
           从碳流向结果看，排放贡献主要集中在生产环节与仓储配送环节，其中范围一排放和范围三排放占比较高，说明企业后续应重点围绕燃料使用、物流运输及供应链协同开展减排优化。
        </div>
    `;

    host.insertAdjacentElement('afterend', section);
    renderCarbonFlowChart();
}
function renderCarbonFlowChart() {
    const chartDom = document.getElementById('carbonFlowChart');
    if (!chartDom || typeof echarts === 'undefined') return;

    const chart = echarts.init(chartDom);

    const option = {
        backgroundColor: 'transparent',
        animationDuration: 900,
       tooltip: {
    trigger: 'item',
    triggerOn: 'mousemove',
    formatter: function (params) {
        if (params.dataType === 'edge') {
            return `${params.data.source} → ${params.data.target}<br/>流量值：${params.data.value}`;
        }
        return `${params.name}`;
    }
},
        series: [
            {
                levels: [
    {
        depth: 0,
        itemStyle: { color: '#8FA4B8' },
        lineStyle: { opacity: 0.28 }
    },
    {
        depth: 1,
        itemStyle: { color: '#7BAE7F' },
        lineStyle: { opacity: 0.32 }
    },
    {
        depth: 2,
        itemStyle: { color: '#D19A52' },
        lineStyle: { opacity: 0.36 }
    },
    {
        depth: 3,
        itemStyle: { color: '#5B7FA3' },
        lineStyle: { opacity: 0.4 }
    }
],
                type: 'sankey',
                layout: 'none',
                emphasis: {
                    focus: 'adjacency'
                },
                data: [
    { name: '外购电力' },
    { name: '燃料消耗' },
    { name: '物流运输' },
    { name: '包装材料' },
    { name: '采购环节' },
    { name: '生产环节' },
    { name: '仓储配送' },
    { name: '范围一排放' },
    { name: '范围二排放' },
    { name: '范围三排放' },
    { name: '总碳排放' }
],
                links: [
    { source: '外购电力', target: '采购环节', value: 18 },
    { source: '燃料消耗', target: '生产环节', value: 26 },
    { source: '物流运输', target: '仓储配送', value: 14 },
    { source: '包装材料', target: '仓储配送', value: 8 },

    { source: '采购环节', target: '范围二排放', value: 18 },
    { source: '生产环节', target: '范围一排放', value: 26 },
    { source: '仓储配送', target: '范围三排放', value: 22 },

    { source: '范围一排放', target: '总碳排放', value: 26 },
    { source: '范围二排放', target: '总碳排放', value: 18 },
    { source: '范围三排放', target: '总碳排放', value: 22 }
],
                nodeAlign: 'justify',
                draggable: true,
                left: 20,
                right: 20,
                top: 20,
                bottom: 20,
              lineStyle: {
    color: 'gradient',
    curveness: 0.42,
    opacity: 0.32
},
                itemStyle: {
    borderWidth: 1,
    borderColor: '#d7dee8',
    color: '#7b8da6'
},
               label: {
    color: '#344054',
    fontSize: 12,
    fontWeight: 600
},
            }
        ]
    };

    chart.setOption(option);

    window.addEventListener('resize', () => {
        chart.resize();
    });
}
// --- 模式切换逻辑 ---
let currentTwinMode = 'total';
let originalMaterials = new Map();

function switchTwinMode(mode) {
        console.log('Switching to mode:', mode);
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
                if(mesh.material.color) if(mesh.material.color) mesh.material.color.setHex(originalMaterials.get(mesh.uuid));
                if(mesh.material.emissive) if(mesh.material.emissive) mesh.material.emissive.setHex(0x000000);
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
                if(mesh.material.color) if(mesh.material.color) mesh.material.color.setHex(0xff3333);
                if(mesh.material.emissive) if(mesh.material.emissive) mesh.material.emissive.setHex(0x440000); // 红光发热
            }
        });
    }
    else if (mode === 'esg') {
        if(b3) { b3.classList.add('active', 'border-success'); b3.classList.remove('border-secondary'); }
        if(expDom) expDom.innerHTML = '<i class="fas fa-leaf text-success me-1"></i> 设备均已接入绿电网络，S(社会)无安全事故，G(治理)数据实时上链防篡改。';
        
        // 恢复原有材质颜色，发绿光
        factoryGroup.children.forEach(mesh => {
            if (originalMaterials.has(mesh.uuid)) {
                if(mesh.material.color) if(mesh.material.color) mesh.material.color.setHex(0x225522);
                if(mesh.material.emissive) if(mesh.material.emissive) mesh.material.emissive.setHex(0x002200);
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
