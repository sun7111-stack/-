(function () {
    if (window.__advancedInteractionsInstalled) return;
    window.__advancedInteractionsInstalled = true;

    const pages = [
        { id: 'home', label: '首页概览', group: '总览', icon: 'fa-home' },
        { id: 'demo-upload', label: '上传识别', group: '核心业务流', icon: 'fa-file-invoice' },
        { id: 'demo-carbon', label: '自动化碳核算', group: '核心业务流', icon: 'fa-calculator' },
        { id: 'demo-risk', label: '风控检测', group: '核心业务流', icon: 'fa-shield-alt' },
        { id: 'demo-report', label: 'AI诊断报告', group: '核心业务流', icon: 'fa-robot' },
        { id: 'features', label: '产品功能', group: '数据管理', icon: 'fa-cube' },
        { id: 'esg-calculator', label: 'ESG智能计算器', group: '数据管理', icon: 'fa-chart-pie' },
        { id: 'data-center', label: '数据报告中心', group: '数据管理', icon: 'fa-file-alt' },
        { id: 'finance-match', label: '绿色金融对接', group: '数据管理', icon: 'fa-handshake' },
        { id: 'solutions', label: '行业解决方案', group: '行业服务', icon: 'fa-gem' },
        { id: 'cases', label: '客户成功案例', group: '行业服务', icon: 'fa-briefcase' },
        { id: 'settings', label: '系统设置', group: '系统', icon: 'fa-cog' }
    ];

    const pageMap = new Map(pages.map(page => [page.id, page]));
    let activeResultIndex = 0;
    let paletteResults = [];

    function currentPageId() {
        return window.location.hash.replace('#', '') || 'home';
    }

    function currentPage() {
        return pageMap.get(currentPageId()) || pageMap.get('home');
    }

    function createShell() {
        if (!document.querySelector('.experience-aura')) {
            document.body.insertAdjacentHTML('afterbegin', '<div class="experience-aura" aria-hidden="true"></div><div class="interaction-progress" aria-hidden="true"><i></i></div>');
        }

        if (!document.getElementById('routeFlash')) {
            document.body.insertAdjacentHTML('beforeend', '<div class="route-flash" id="routeFlash"><i class="fas fa-location-dot"></i><span></span></div>');
        }

        if (!document.getElementById('interactionDock')) {
            document.body.insertAdjacentHTML('beforeend', `
                <div class="interaction-dock" id="interactionDock">
                    <div class="interaction-dock-panel">
                        <div class="dock-title">
                            <div>
                                <strong id="dockPageTitle">当前页面</strong>
                                <span id="dockPageGroup">工作区</span>
                            </div>
                            <button class="btn btn-sm btn-outline-success" type="button" id="dockPaletteBtn">Ctrl K</button>
                        </div>
                        <div class="dock-shortcuts">
                            <button type="button" data-jump="demo-upload">上传识别</button>
                            <button type="button" data-jump="demo-carbon">碳核算</button>
                            <button type="button" data-jump="data-center">报告中心</button>
                            <button type="button" data-jump="finance-match">金融对接</button>
                        </div>
                    </div>
                    <button class="interaction-dock-trigger" type="button" aria-label="打开交互面板">
                        <i class="fas fa-wand-magic-sparkles"></i>
                    </button>
                </div>
            `);
        }

        if (!document.getElementById('interactionPalette')) {
            document.body.insertAdjacentHTML('beforeend', `
                <div class="interaction-palette" id="interactionPalette" aria-hidden="true">
                    <div class="palette-card" role="dialog" aria-label="快速导航">
                        <div class="palette-input-row">
                            <i class="fas fa-search"></i>
                            <input id="paletteInput" type="text" placeholder="搜索页面、功能或模块..." autocomplete="off">
                        </div>
                        <div class="palette-results" id="paletteResults"></div>
                    </div>
                </div>
            `);
        }

        if (!document.getElementById('interactionRouteChip')) {
            const navRight = document.querySelector('.top-navbar .navbar-right');
            if (navRight) {
                navRight.insertAdjacentHTML('afterbegin', '<div class="interaction-route-chip" id="interactionRouteChip"><i class="fas fa-circle-nodes"></i><span></span></div>');
            }
        }
    }

    function updateProgress() {
        const scrollable = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
        const progress = Math.min(100, Math.max(0, (window.scrollY / scrollable) * 100));
        document.documentElement.style.setProperty('--scroll-progress', `${progress}%`);
    }

    function updatePointer(event) {
        document.documentElement.style.setProperty('--ix', `${event.clientX}px`);
        document.documentElement.style.setProperty('--iy', `${event.clientY}px`);
    }

    function addSurfaceTracking() {
        const selector = [
            '.card',
            '.feature-card',
            '.solution-card',
            '.pricing-card',
            '.finance-card',
            '.report-type-card',
            '.template-card',
            '.calculator-container',
            '.report-generator',
            '.premium-context-header',
            '.stat-card'
        ].join(',');

        document.querySelectorAll(selector).forEach(element => {
            if (element.dataset.advancedSurfaceBound) return;
            element.dataset.advancedSurfaceBound = 'true';
            element.classList.add('advanced-surface');
            element.addEventListener('pointermove', event => {
                const rect = element.getBoundingClientRect();
                const mx = ((event.clientX - rect.left) / Math.max(rect.width, 1)) * 100;
                const my = ((event.clientY - rect.top) / Math.max(rect.height, 1)) * 100;
                element.style.setProperty('--mx', `${mx}%`);
                element.style.setProperty('--my', `${my}%`);
            });
        });

        document.querySelectorAll('.menu-link').forEach(link => {
            if (link.dataset.advancedMenuBound) return;
            link.dataset.advancedMenuBound = 'true';
            link.addEventListener('pointermove', event => {
                const rect = link.getBoundingClientRect();
                link.style.setProperty('--mx', `${((event.clientX - rect.left) / Math.max(rect.width, 1)) * 100}%`);
                link.style.setProperty('--my', `${((event.clientY - rect.top) / Math.max(rect.height, 1)) * 100}%`);
            });
        });
    }

    function navigateTo(id) {
        const target = document.querySelector(`[data-page="${id}"]`) || document.querySelector(`a[href="#${id}"]`);
        if (target && target.click) {
            target.click();
        } else {
            window.location.hash = id;
        }
        closePalette();
        document.getElementById('interactionDock')?.classList.remove('open');
        setTimeout(syncPageState, 40);
    }

    function showRouteFlash(page) {
        const flash = document.getElementById('routeFlash');
        if (!flash) return;
        flash.querySelector('span').textContent = `${page.group} / ${page.label}`;
        flash.classList.remove('show');
        void flash.offsetWidth;
        flash.classList.add('show');
    }

    function syncPageState(showFlash = false) {
        const page = currentPage();
        const chip = document.getElementById('interactionRouteChip');
        if (chip) chip.querySelector('span').textContent = `${page.group} / ${page.label}`;

        const title = document.getElementById('dockPageTitle');
        const group = document.getElementById('dockPageGroup');
        if (title) title.textContent = page.label;
        if (group) group.textContent = page.group;

        document.querySelectorAll('.menu-item').forEach(item => {
            const link = item.querySelector('a[href^="#"]');
            item.classList.toggle('active', link?.getAttribute('href') === `#${page.id}`);
        });

        if (showFlash) showRouteFlash(page);
        setTimeout(addSurfaceTracking, 120);
    }

    function openPalette() {
        const palette = document.getElementById('interactionPalette');
        const input = document.getElementById('paletteInput');
        if (!palette || !input) return;
        palette.classList.add('open');
        palette.setAttribute('aria-hidden', 'false');
        input.value = '';
        renderPalette('');
        activeResultIndex = 0;
        setTimeout(() => input.focus(), 30);
    }

    function closePalette() {
        const palette = document.getElementById('interactionPalette');
        if (!palette) return;
        palette.classList.remove('open');
        palette.setAttribute('aria-hidden', 'true');
    }

    function renderPalette(query) {
        const results = document.getElementById('paletteResults');
        if (!results) return;

        const q = query.trim().toLowerCase();
        paletteResults = pages.filter(page => {
            const haystack = `${page.id} ${page.label} ${page.group}`.toLowerCase();
            return !q || haystack.includes(q);
        }).slice(0, 8);

        if (!paletteResults.length) {
            results.innerHTML = '<div class="palette-result"><i class="fas fa-circle-info"></i><div><strong>没有匹配页面</strong><span>换一个关键词试试</span></div></div>';
            return;
        }

        results.innerHTML = paletteResults.map((page, index) => `
            <button type="button" class="palette-result ${index === activeResultIndex ? 'active' : ''}" data-palette-jump="${page.id}">
                <i class="fas ${page.icon}"></i>
                <div>
                    <strong>${page.label}</strong>
                    <span>${page.group} · #${page.id}</span>
                </div>
            </button>
        `).join('');
    }

    function bindEvents() {
        window.addEventListener('scroll', updateProgress, { passive: true });
        window.addEventListener('pointermove', updatePointer, { passive: true });
        window.addEventListener('hashchange', () => {
            document.body.classList.add('page-switching');
            setTimeout(() => document.body.classList.remove('page-switching'), 420);
            syncPageState(true);
        });

        document.addEventListener('click', event => {
            const dockTrigger = event.target.closest('.interaction-dock-trigger');
            if (dockTrigger) {
                document.getElementById('interactionDock')?.classList.toggle('open');
                return;
            }

            const dockJump = event.target.closest('[data-jump]');
            if (dockJump) {
                navigateTo(dockJump.getAttribute('data-jump'));
                return;
            }

            if (event.target.closest('#dockPaletteBtn')) {
                openPalette();
                return;
            }

            const paletteJump = event.target.closest('[data-palette-jump]');
            if (paletteJump) {
                navigateTo(paletteJump.getAttribute('data-palette-jump'));
                return;
            }

            const palette = document.getElementById('interactionPalette');
            if (palette?.classList.contains('open') && event.target === palette) {
                closePalette();
            }
        });

        document.addEventListener('keydown', event => {
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
                event.preventDefault();
                openPalette();
                return;
            }

            const palette = document.getElementById('interactionPalette');
            if (!palette?.classList.contains('open')) return;

            if (event.key === 'Escape') {
                closePalette();
                return;
            }

            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                event.preventDefault();
                const step = event.key === 'ArrowDown' ? 1 : -1;
                activeResultIndex = Math.max(0, Math.min(paletteResults.length - 1, activeResultIndex + step));
                renderPalette(document.getElementById('paletteInput')?.value || '');
                return;
            }

            if (event.key === 'Enter' && paletteResults[activeResultIndex]) {
                navigateTo(paletteResults[activeResultIndex].id);
            }
        });

        document.addEventListener('input', event => {
            if (event.target?.id === 'paletteInput') {
                activeResultIndex = 0;
                renderPalette(event.target.value);
            }
        });
    }

    function wrapSwitchPage() {
        if (typeof window.switchPage !== 'function' || window.switchPage.__advancedInteractionsWrapped) return;
        const originalSwitchPage = window.switchPage;
        window.switchPage = function () {
            document.body.classList.add('page-switching');
            const result = originalSwitchPage.apply(this, arguments);
            setTimeout(() => {
                document.body.classList.remove('page-switching');
                syncPageState(true);
            }, 220);
            return result;
        };
        window.switchPage.__advancedInteractionsWrapped = true;
    }

    document.addEventListener('DOMContentLoaded', () => {
        createShell();
        bindEvents();
        wrapSwitchPage();
        updateProgress();
        syncPageState(false);
        addSurfaceTracking();
        setTimeout(addSurfaceTracking, 600);
    });
})();
