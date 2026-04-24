(function () {
    const pageConfig = {
        features: {
            icon: 'fa-cube',
            kicker: 'Product Matrix',
            title: '产品功能工作台',
            subtitle: '用一条清晰的数据链路组织识别、核算、评分、报告，不再把能力拆成孤立模块。',
            variant: 'flow',
            metrics: [['OCR', '票据识别'], ['Carbon', '碳核算'], ['ESG', '动态评分'], ['Report', '报告生成']]
        },
        'esg-calculator': {
            icon: 'fa-calculator',
            kicker: 'ESG Scoring',
            title: 'ESG智能计算器',
            subtitle: '把三维评分、权重和改进建议压到一个判断界面里，适合快速复盘企业当前表现。',
            variant: 'score',
            metrics: [['E', '85'], ['S', '72'], ['G', '90'], ['Level', 'A']]
        },
        'data-center': {
            icon: 'fa-file-alt',
            kicker: 'Report Operations',
            title: '数据报告中心',
            subtitle: '围绕模板选择、AI生成、预览修订和导出归档建立一条更像生产线的报告流程。',
            variant: 'report',
            metrics: [['Template', '选择'], ['Draft', '生成'], ['Review', '校验'], ['Export', '归档']]
        },
        'finance-match': {
            icon: 'fa-handshake',
            kicker: 'Green Finance',
            title: '绿色金融对接',
            subtitle: '突出产品匹配度、授信额度和利率优势，让金融产品之间的差异更容易比较。',
            variant: 'finance',
            metrics: [['98%', '最佳匹配'], ['3.65%', '参考利率'], ['500万', '授信额度'], ['A', 'ESG评级']]
        },
        solutions: {
            icon: 'fa-gem',
            kicker: 'Industry Playbooks',
            title: '行业解决方案',
            subtitle: '按业务场景组织碳数据采集、核算边界、合规输出和金融材料，让方案看起来像能直接落地的作业台。',
            variant: 'industry',
            metrics: [['电商', '订单与包装'], ['制造', '能耗与供应链'], ['物流', '路线与车队'], ['定价', '按规模选择']]
        }
    };

    const state = {
        pointer: { x: 0, y: 0 },
        scenes: new Map()
    };

    function pageSection(id) {
        return document.getElementById(id);
    }

    function visualMarkup(config, id) {
        if (config.variant === 'flow') {
            return `
                <div class="premium-context-visual premium-flow-visual" data-premium-visual="${id}">
                    ${config.metrics.map(([value, label], index) => `
                        <div class="flow-token" style="--i:${index}">
                            <strong>${value}</strong>
                            <span>${label}</span>
                        </div>
                    `).join('')}
                    <div class="flow-thread"></div>
                </div>
            `;
        }

        if (config.variant === 'score') {
            return `
                <div class="premium-context-visual premium-score-visual">
                    ${config.metrics.slice(0, 3).map(([label, value], index) => `
                        <div class="score-orbit score-orbit-${index + 1}" style="--score:${value}">
                            <span>${label}</span>
                            <strong>${value}</strong>
                        </div>
                    `).join('')}
                    <div class="score-grade">
                        <span>综合评级</span>
                        <strong>A</strong>
                    </div>
                </div>
            `;
        }

        if (config.variant === 'report') {
            return `
                <div class="premium-context-visual premium-report-visual">
                    ${config.metrics.map(([value, label], index) => `
                        <div class="report-sheet report-sheet-${index + 1}">
                            <span>${value}</span>
                            <strong>${label}</strong>
                            <i></i>
                            <i></i>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        if (config.variant === 'industry') {
            return `
                <div class="premium-context-visual premium-industry-visual">
                    ${config.metrics.map(([value, label], index) => `
                        <div class="industry-signal industry-signal-${index + 1}">
                            <span>${label}</span>
                            <strong>${value}</strong>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        return `
            <div class="premium-context-visual premium-finance-visual">
                ${config.metrics.map(([value, label], index) => `
                    <div class="finance-lane finance-lane-${index + 1}">
                        <span>${label}</span>
                        <strong>${value}</strong>
                    </div>
                `).join('')}
            </div>
        `;
    }

    function createContextHeader(id, config) {
        const section = pageSection(id);
        if (!section || section.querySelector('.premium-context-header')) return;

        section.classList.add('premium-upgraded', `premium-${config.variant}`);
        const container = section.querySelector(':scope > .container') || section;
        const header = document.createElement('div');
        header.className = `premium-context-header premium-tilt premium-context-${config.variant}`;
        header.innerHTML = `
            <div class="premium-context-copy">
                <div class="premium-page-kicker"><i class="fas ${config.icon}"></i>${config.kicker}</div>
                <h1 class="premium-page-title">${config.title}</h1>
                <p class="premium-page-subtitle">${config.subtitle}</p>
            </div>
            ${visualMarkup(config, id)}
        `;

        container.insertBefore(header, container.firstElementChild);
    }

    function initFlowScene(id, host) {
        if (!window.THREE || !host || state.scenes.has(id)) return;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(38, host.clientWidth / Math.max(host.clientHeight, 1), 0.1, 80);
        camera.position.set(0, 0.4, 7.2);

        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.setSize(host.clientWidth, host.clientHeight);
        host.appendChild(renderer.domElement);

        const root = new THREE.Group();
        scene.add(root);
        scene.add(new THREE.AmbientLight(0xffffff, 0.7));
        const light = new THREE.DirectionalLight(0xbff8ef, 1.1);
        light.position.set(4, 5, 6);
        scene.add(light);

        const nodeMaterial = new THREE.MeshStandardMaterial({
            color: 0x1f7a59,
            metalness: 0.36,
            roughness: 0.28,
            emissive: 0x0f5b43,
            emissiveIntensity: 0.35
        });
        const accentMaterial = new THREE.MeshStandardMaterial({
            color: 0x3aa0a8,
            metalness: 0.42,
            roughness: 0.24,
            emissive: 0x0b5360,
            emissiveIntensity: 0.32
        });
        const geometry = new THREE.IcosahedronGeometry(0.11, 1);
        const positions = [[-2.55, 0.42, 0], [-0.86, -0.15, 0.28], [0.82, 0.2, -0.2], [2.42, -0.22, 0.16]];
        const nodes = positions.map((position, index) => {
            const mesh = new THREE.Mesh(geometry, index === 2 ? accentMaterial : nodeMaterial);
            mesh.position.set(position[0], position[1], position[2]);
            mesh.userData.phase = index * 0.7;
            root.add(mesh);
            return mesh;
        });

        const lineMaterial = new THREE.LineBasicMaterial({ color: 0x7bd8cf, transparent: true, opacity: 0.35 });
        for (let i = 0; i < nodes.length - 1; i += 1) {
            root.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([nodes[i].position, nodes[i + 1].position]), lineMaterial));
        }

        const particleGeometry = new THREE.BufferGeometry();
        const count = 80;
        const positionsArray = new Float32Array(count * 3);
        for (let i = 0; i < count; i += 1) {
            positionsArray[i * 3] = -2.8 + Math.random() * 5.6;
            positionsArray[i * 3 + 1] = -0.65 + Math.random() * 1.35;
            positionsArray[i * 3 + 2] = -0.45 + Math.random() * 0.9;
        }
        particleGeometry.setAttribute('position', new THREE.BufferAttribute(positionsArray, 3));
        const particles = new THREE.Points(
            particleGeometry,
            new THREE.PointsMaterial({ color: 0x9be7d8, size: 0.018, transparent: true, opacity: 0.55 })
        );
        root.add(particles);

        const clock = new THREE.Clock();
        let frameId = 0;
        function resize() {
            if (!host.clientWidth || !host.clientHeight) return;
            camera.aspect = host.clientWidth / host.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(host.clientWidth, host.clientHeight);
        }
        function render() {
            const time = clock.getElapsedTime();
            root.rotation.y = state.pointer.x * 0.08;
            root.rotation.x = state.pointer.y * 0.04;
            nodes.forEach(node => node.scale.setScalar(1 + Math.sin(time * 2 + node.userData.phase) * 0.08));
            particles.rotation.z = time * 0.025;
            renderer.render(scene, camera);
            frameId = requestAnimationFrame(render);
        }

        let observer = null;
        if ('ResizeObserver' in window) {
            observer = new ResizeObserver(resize);
            observer.observe(host);
        }
        state.scenes.set(id, { resize, stop: () => { cancelAnimationFrame(frameId); if (observer) observer.disconnect(); } });
        resize();
        render();
    }

    function bindTilt() {
        const selector = '.premium-tilt, .premium-upgraded .feature-card, .premium-upgraded .report-type-card, .premium-upgraded .template-card, .premium-upgraded .finance-card';
        document.querySelectorAll(selector).forEach(element => {
            if (element.dataset.premiumTiltBound) return;
            element.dataset.premiumTiltBound = 'true';
            element.addEventListener('pointermove', event => {
                if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
                const rect = element.getBoundingClientRect();
                const x = (event.clientX - rect.left) / rect.width - 0.5;
                const y = (event.clientY - rect.top) / rect.height - 0.5;
                element.style.transform = `perspective(900px) rotateX(${(-y * 2.4).toFixed(2)}deg) rotateY(${(x * 3).toFixed(2)}deg) translateY(-2px)`;
            });
            element.addEventListener('pointerleave', () => {
                element.style.transform = '';
            });
        });
    }

    function installReveal() {
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });

        Object.keys(pageConfig).forEach(id => {
            const section = pageSection(id);
            if (!section) return;
            section.querySelectorAll('.row, .report-generator, .calculator-container, .finance-card, .feature-demo').forEach(node => {
                if (node.dataset.premiumRevealBound) return;
                node.dataset.premiumRevealBound = 'true';
                node.classList.add('premium-reveal');
                observer.observe(node);
            });
        });
    }

    function resizeScenes() {
        state.scenes.forEach(scene => scene.resize());
    }

    function enhancePages() {
        Object.entries(pageConfig).forEach(([id, config]) => {
            createContextHeader(id, config);
            if (config.variant === 'flow') {
                initFlowScene(id, document.querySelector(`[data-premium-visual="${id}"]`));
            }
        });
        bindTilt();
        installReveal();
        resizeScenes();
    }

    document.addEventListener('pointermove', event => {
        state.pointer.x = (event.clientX / Math.max(window.innerWidth, 1) - 0.5) * 2;
        state.pointer.y = (event.clientY / Math.max(window.innerHeight, 1) - 0.5) * 2;
    }, { passive: true });

    window.addEventListener('resize', resizeScenes);
    window.addEventListener('hashchange', () => setTimeout(resizeScenes, 160));

    document.addEventListener('DOMContentLoaded', () => {
        enhancePages();
        setTimeout(resizeScenes, 300);
        if (typeof window.switchPage === 'function' && !window.switchPage.__premiumResizeWrapped) {
            const originalSwitchPage = window.switchPage;
            window.switchPage = function () {
                const result = originalSwitchPage.apply(this, arguments);
                setTimeout(resizeScenes, 180);
                return result;
            };
            window.switchPage.__premiumResizeWrapped = true;
        }
    });
})();
