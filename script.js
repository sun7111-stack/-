// ============================================
// 碳融智核平台 - 主交互脚本
// 版本: 2.0.0
// 最后更新: 2024-01-18
// ============================================

// 全局变量和配置
// ============================================
// 登录状态与页面路由管理
// ============================================

// 登录状态检查
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    initLoginPage();
    initSidebar();
    initPageRouter();
});

// 检查登录状态
function checkLoginStatus() {
    const isLoggedIn = localStorage.getItem('carbon_platform_logged_in') === 'true';
    const loginPage = document.getElementById('loginPage');
    const appMain = document.getElementById('appMain');
    
    if (isLoggedIn) {
        loginPage.style.display = 'none';
        appMain.style.display = 'flex';
        loadUserInfo();
    } else {
        loginPage.style.display = 'flex';
        appMain.style.display = 'none';
    }
}

// 初始化登录页面
function initLoginPage() {
    // 登录表单提交
    const loginForm = document.getElementById('loginFormContent');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = this.querySelector('input[type="email"]').value;
            const password = this.querySelector('input[type="password"]').value;
            const rememberMe = this.querySelector('#rememberMe').checked;
            const loginBtn = this.querySelector('button[type="submit"]');
            const originalText = loginBtn.innerHTML;
            
            loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>登录中...';
            loginBtn.disabled = true;
            
            // 调用后端API登录
            API.login(email, password).then(data => {
                localStorage.setItem('carbon_platform_logged_in', 'true');
                if (rememberMe) {
                    localStorage.setItem('carbon_platform_remember_email', email);
                }
                PlatformState.user = {
                    id: data.user.id,
                    email: data.user.email,
                    name: data.user.name,
                    company: data.user.company || '',
                    type: data.user.company_type || 'ecommerce',
                    loginTime: new Date().toISOString()
                };
                saveUserData();
                checkLoginStatus();
                showToast(`登录成功！欢迎回来，${data.user.name}`, 'success');
                initPlatform();
            }).catch(err => {
                showToast(err.message || '邮箱或密码错误，请重试', 'error');
            }).finally(() => {
                loginBtn.innerHTML = originalText;
                loginBtn.disabled = false;
            });
        });
    }
    
    // 注册表单提交
    const registerForm = document.getElementById('registerFormContent');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const name = this.querySelectorAll('input[type="text"]')[0].value;
            const company = this.querySelectorAll('input[type="text"]')[1].value;
            const email = this.querySelector('input[type="email"]').value;
            const password = this.querySelectorAll('input[type="password"]')[0].value;
            const confirmPassword = this.querySelectorAll('input[type="password"]')[1].value;
            const registerBtn = this.querySelector('button[type="submit"]');
            const originalText = registerBtn.innerHTML;
            
            if (password !== confirmPassword) {
                showToast('两次输入的密码不一致', 'error');
                return;
            }
            
            registerBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>注册中...';
            registerBtn.disabled = true;
            
            // 调用后端API注册
            API.register({ name, company, email, password }).then(data => {
                localStorage.setItem('carbon_platform_logged_in', 'true');
                PlatformState.user = {
                    id: data.user.id,
                    email: data.user.email,
                    name: data.user.name,
                    company: data.user.company || '',
                    type: data.user.company_type || 'ecommerce',
                    loginTime: new Date().toISOString()
                };
                saveUserData();
                checkLoginStatus();
                showToast(`注册成功！欢迎加入碳融智核，${data.user.name}`, 'success');
                initPlatform();
            }).catch(err => {
                showToast(err.message || '注册失败，请重试', 'error');
            }).finally(() => {
                registerBtn.innerHTML = originalText;
                registerBtn.disabled = false;
            });
        });
    }
    
    // 登录/注册标签切换
    const loginTabs = document.querySelectorAll('.login-page .login-tab');
    loginTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const target = this.getAttribute('data-tab');
            loginTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            document.querySelectorAll('.login-page .login-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${target}Form`).classList.add('active');
        });
    });
    
    // 退出登录
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            API.logout();
            localStorage.removeItem('carbon_platform_logged_in');
            PlatformState.user = null;
            checkLoginStatus();
            showToast('已成功退出登录', 'success');
        });
    }
}

// 初始化侧边栏
function initSidebar() {
    // 侧边栏折叠/展开
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const body = document.querySelector('body');
    
    if (sidebarToggle && sidebar) {
        // 创建遮罩层
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        body.appendChild(overlay);
        
        sidebarToggle.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                // 移动端：打开/关闭侧边栏
                sidebar.classList.toggle('open');
                overlay.classList.toggle('show');
            } else {
                // 桌面端：折叠/展开
                sidebar.classList.toggle('collapsed');
            }
        });
        
        // 点击遮罩层关闭侧边栏
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
        });
    }
}

// 初始化页面路由
function initPageRouter() {
    const menuItems = document.querySelectorAll('.menu-item');
    const pageSections = document.querySelectorAll('.page-section');
    const pageLinks = document.querySelectorAll('.page-link');
    
    // 菜单点击切换页面
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const targetPage = this.getAttribute('data-page');
            switchPage(targetPage);
            
            // 更新菜单激活状态
            menuItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // 移动端关闭侧边栏
            const sidebar = document.getElementById('sidebar');
            const overlay = document.querySelector('.sidebar-overlay');
            if (window.innerWidth <= 768 && sidebar && overlay) {
                sidebar.classList.remove('open');
                overlay.classList.remove('show');
            }
        });
    });
    
    // 页面内链接跳转
    pageLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetPage = this.getAttribute('data-page');
            if (targetPage) {
                switchPage(targetPage);
                menuItems.forEach(item => {
                    item.classList.remove('active');
                    if (item.getAttribute('data-page') === targetPage) {
                        item.classList.add('active');
                    }
                });
            }
        });
    });
    
    // 锚点链接处理
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#' || href.startsWith('#!')) return;
            
            const targetSection = document.querySelector(href);
            if (targetSection && targetSection.classList.contains('page-section')) {
                e.preventDefault();
                switchPage(href.substring(1));
                menuItems.forEach(item => {
                    item.classList.remove('active');
                    if (item.getAttribute('data-page') === href.substring(1)) {
                        item.classList.add('active');
                    }
                });
            }
        });
    });
}

// 页面切换函数
function switchPage(pageId) {
    const pageSections = document.querySelectorAll('.page-section');
    const targetPage = document.getElementById(pageId);
    
    if (!targetPage) return;
    
    // 隐藏所有页面
    pageSections.forEach(section => {
        section.classList.remove('active');
    });
    
    // 显示目标页面
    targetPage.classList.add('active');
    
    // 更新URL hash
    window.history.pushState(null, null, `#${pageId}`);
    
    // 页面切换后重新初始化图表
    setTimeout(() => {
        if (pageId === 'home') initHeroDashboard();
        if (pageId === 'features') initDashboardDemo();
        if (pageId === 'esg-calculator') {
            initESGRadarChart();
            updateESGVisualization();
        }
        window.dispatchEvent(new Event('resize'));
    }, 100);
}

// 加载用户信息
function loadUserInfo() {
    if (!PlatformState.user) return;
    
    const userNameEl = document.getElementById('userName');
    const accountNameEl = document.getElementById('accountName');
    const accountEmailEl = document.getElementById('accountEmail');
    const companyNameEl = document.getElementById('companyName');
    
    if (userNameEl) userNameEl.textContent = PlatformState.user.name;
    if (accountNameEl) accountNameEl.value = PlatformState.user.name;
    if (accountEmailEl) accountEmailEl.value = PlatformState.user.email;
    if (companyNameEl) companyNameEl.value = PlatformState.user.company;
}

// 快速碳计算
function quickCalculateCarbon() {
    const electricity = parseFloat(document.getElementById('quickElectricity').value) || 0;
    const gas = parseFloat(document.getElementById('quickGas').value) || 0;
    const gasoline = parseFloat(document.getElementById('quickGasoline').value) || 0;
    const diesel = parseFloat(document.getElementById('quickDiesel').value) || 0;
    
    const factors = DataService.emissionFactors;
    const totalCarbon = 
        (electricity * factors.electricity) +
        (gas * factors.natural_gas) +
        (gasoline * factors.gasoline) +
        (diesel * factors.diesel);
    
    const resultHtml = `
        <div class="alert alert-success">
            <h5><i class="fas fa-check-circle me-2"></i>计算完成</h5>
            <div class="row mt-3">
                <div class="col-6">
                    <p class="mb-1"><strong>总碳排放量：</strong></p>
                    <h3 class="text-primary">${totalCarbon.toFixed(2)} kgCO₂</h3>
                </div>
                <div class="col-6">
                    <p class="mb-1"><strong>换算为吨：</strong></p>
                    <h3 class="text-success">${(totalCarbon / 1000).toFixed(4)} tCO₂</h3>
                </div>
            </div>
        </div>
        <div class="row g-3 mt-2">
            <div class="col-md-3">
                <div class="stat-item">
                    <div class="stat-value">${(electricity * factors.electricity).toFixed(2)}</div>
                    <div class="stat-label">电力排放</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-item">
                    <div class="stat-value">${(gas * factors.natural_gas).toFixed(2)}</div>
                    <div class="stat-label">天然气排放</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-item">
                    <div class="stat-value">${(gasoline * factors.gasoline).toFixed(2)}</div>
                    <div class="stat-label">汽油排放</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-item">
                    <div class="stat-value">${(diesel * factors.diesel).toFixed(2)}</div>
                    <div class="stat-label">柴油排放</div>
                </div>
            </div>
        </div>
        <div class="text-center mt-4">
            <button class="btn btn-primary me-2" onclick="openCalculator('esg')">
                <i class="fas fa-chart-bar me-2"></i>查看详细ESG计算
            </button>
            <button class="btn btn-outline-primary" onclick="generateReport('basic')">
                <i class="fas fa-file-alt me-2"></i>生成碳排放报告
            </button>
        </div>
    `;
    
    document.getElementById('quickCalcResult').innerHTML = resultHtml;
}
const CONFIG = {
    API_BASE_URL: 'https://api.carbon-ai.com/v1',
    LOCAL_STORAGE_KEY: 'carbon_platform_data',
    THEME_KEY: 'carbon_platform_theme',
    USER_KEY: 'carbon_platform_user',
    VERSION: '2.0.0'
};

// 平台状态管理
// ============================================
// 登录状态与页面路由管理
// ============================================

// 登录状态检查
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    initLoginPage();
    initSidebar();
    initPageRouter();
});

// 检查登录状态
function checkLoginStatus() {
    const isLoggedIn = localStorage.getItem('carbon_platform_logged_in') === 'true';
    const loginPage = document.getElementById('loginPage');
    const appMain = document.getElementById('appMain');
    
    if (isLoggedIn) {
        loginPage.style.display = 'none';
        appMain.style.display = 'flex';
        loadUserInfo();
    } else {
        loginPage.style.display = 'flex';
        appMain.style.display = 'none';
    }
}

// 初始化登录页面
function initLoginPage() {
    // 登录表单提交
    const loginForm = document.getElementById('loginFormContent');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = this.querySelector('input[type="email"]').value;
            const password = this.querySelector('input[type="password"]').value;
            const rememberMe = this.querySelector('#rememberMe').checked;
            const loginBtn = this.querySelector('button[type="submit"]');
            const originalText = loginBtn.innerHTML;
            
            loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>登录中...';
            loginBtn.disabled = true;
            
            // 调用后端API登录
            API.login(email, password).then(data => {
                localStorage.setItem('carbon_platform_logged_in', 'true');
                if (rememberMe) {
                    localStorage.setItem('carbon_platform_remember_email', email);
                }
                PlatformState.user = {
                    id: data.user.id,
                    email: data.user.email,
                    name: data.user.name,
                    company: data.user.company || '',
                    type: data.user.company_type || 'ecommerce',
                    loginTime: new Date().toISOString()
                };
                saveUserData();
                checkLoginStatus();
                showToast(`登录成功！欢迎回来，${data.user.name}`, 'success');
                initPlatform();
            }).catch(err => {
                showToast(err.message || '邮箱或密码错误，请重试', 'error');
            }).finally(() => {
                loginBtn.innerHTML = originalText;
                loginBtn.disabled = false;
            });
        });
    }
    
    // 注册表单提交
    const registerForm = document.getElementById('registerFormContent');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const name = this.querySelectorAll('input[type="text"]')[0].value;
            const company = this.querySelectorAll('input[type="text"]')[1].value;
            const email = this.querySelector('input[type="email"]').value;
            const password = this.querySelectorAll('input[type="password"]')[0].value;
            const confirmPassword = this.querySelectorAll('input[type="password"]')[1].value;
            const registerBtn = this.querySelector('button[type="submit"]');
            const originalText = registerBtn.innerHTML;
            
            if (password !== confirmPassword) {
                showToast('两次输入的密码不一致', 'error');
                return;
            }
            
            registerBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>注册中...';
            registerBtn.disabled = true;
            
            // 调用后端API注册
            API.register({ name, company, email, password }).then(data => {
                localStorage.setItem('carbon_platform_logged_in', 'true');
                PlatformState.user = {
                    id: data.user.id,
                    email: data.user.email,
                    name: data.user.name,
                    company: data.user.company || '',
                    type: data.user.company_type || 'ecommerce',
                    loginTime: new Date().toISOString()
                };
                saveUserData();
                checkLoginStatus();
                showToast(`注册成功！欢迎加入碳融智核，${data.user.name}`, 'success');
                initPlatform();
            }).catch(err => {
                showToast(err.message || '注册失败，请重试', 'error');
            }).finally(() => {
                registerBtn.innerHTML = originalText;
                registerBtn.disabled = false;
            });
        });
    }
    
    // 登录/注册标签切换
    const loginTabs = document.querySelectorAll('.login-page .login-tab');
    loginTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const target = this.getAttribute('data-tab');
            loginTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            document.querySelectorAll('.login-page .login-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${target}Form`).classList.add('active');
        });
    });
    
    // 退出登录
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            API.logout();
            localStorage.removeItem('carbon_platform_logged_in');
            PlatformState.user = null;
            checkLoginStatus();
            showToast('已成功退出登录', 'success');
        });
    }
}

// 初始化侧边栏
function initSidebar() {
    // 侧边栏折叠/展开
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const body = document.querySelector('body');
    
    if (sidebarToggle && sidebar) {
        // 创建遮罩层
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        body.appendChild(overlay);
        
        sidebarToggle.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                // 移动端：打开/关闭侧边栏
                sidebar.classList.toggle('open');
                overlay.classList.toggle('show');
            } else {
                // 桌面端：折叠/展开
                sidebar.classList.toggle('collapsed');
            }
        });
        
        // 点击遮罩层关闭侧边栏
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
        });
    }
}

// 初始化页面路由
function initPageRouter() {
    const menuItems = document.querySelectorAll('.menu-item');
    const pageSections = document.querySelectorAll('.page-section');
    const pageLinks = document.querySelectorAll('.page-link');
    
    // 菜单点击切换页面
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const targetPage = this.getAttribute('data-page');
            switchPage(targetPage);
            
            // 更新菜单激活状态
            menuItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // 移动端关闭侧边栏
            const sidebar = document.getElementById('sidebar');
            const overlay = document.querySelector('.sidebar-overlay');
            if (window.innerWidth <= 768 && sidebar && overlay) {
                sidebar.classList.remove('open');
                overlay.classList.remove('show');
            }
        });
    });
    
    // 页面内链接跳转
    pageLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetPage = this.getAttribute('data-page');
            if (targetPage) {
                switchPage(targetPage);
                menuItems.forEach(item => {
                    item.classList.remove('active');
                    if (item.getAttribute('data-page') === targetPage) {
                        item.classList.add('active');
                    }
                });
            }
        });
    });
    
    // 锚点链接处理
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#' || href.startsWith('#!')) return;
            
            const targetSection = document.querySelector(href);
            if (targetSection && targetSection.classList.contains('page-section')) {
                e.preventDefault();
                switchPage(href.substring(1));
                menuItems.forEach(item => {
                    item.classList.remove('active');
                    if (item.getAttribute('data-page') === href.substring(1)) {
                        item.classList.add('active');
                    }
                });
            }
        });
    });
}

// 页面切换函数
function switchPage(pageId) {
    const pageSections = document.querySelectorAll('.page-section');
    const targetPage = document.getElementById(pageId);
    
    if (!targetPage) return;
    
    // 隐藏所有页面
    pageSections.forEach(section => {
        section.classList.remove('active');
    });
    
    // 显示目标页面
    targetPage.classList.add('active');
    
    // 更新URL hash
    window.history.pushState(null, null, `#${pageId}`);
    
    // 页面切换后重新初始化图表
    setTimeout(() => {
        if (pageId === 'home') initHeroDashboard();
        if (pageId === 'features') initDashboardDemo();
        if (pageId === 'esg-calculator') {
            initESGRadarChart();
            updateESGVisualization();
        }
        window.dispatchEvent(new Event('resize'));
    }, 100);
}

// 加载用户信息
function loadUserInfo() {
    if (!PlatformState.user) return;
    
    const userNameEl = document.getElementById('userName');
    const accountNameEl = document.getElementById('accountName');
    const accountEmailEl = document.getElementById('accountEmail');
    const companyNameEl = document.getElementById('companyName');
    
    if (userNameEl) userNameEl.textContent = PlatformState.user.name;
    if (accountNameEl) accountNameEl.value = PlatformState.user.name;
    if (accountEmailEl) accountEmailEl.value = PlatformState.user.email;
    if (companyNameEl) companyNameEl.value = PlatformState.user.company;
}

// 快速碳计算
function quickCalculateCarbon() {
    const electricity = parseFloat(document.getElementById('quickElectricity').value) || 0;
    const gas = parseFloat(document.getElementById('quickGas').value) || 0;
    const gasoline = parseFloat(document.getElementById('quickGasoline').value) || 0;
    const diesel = parseFloat(document.getElementById('quickDiesel').value) || 0;
    
    const factors = DataService.emissionFactors;
    const totalCarbon = 
        (electricity * factors.electricity) +
        (gas * factors.natural_gas) +
        (gasoline * factors.gasoline) +
        (diesel * factors.diesel);
    
    const resultHtml = `
        <div class="alert alert-success">
            <h5><i class="fas fa-check-circle me-2"></i>计算完成</h5>
            <div class="row mt-3">
                <div class="col-6">
                    <p class="mb-1"><strong>总碳排放量：</strong></p>
                    <h3 class="text-primary">${totalCarbon.toFixed(2)} kgCO₂</h3>
                </div>
                <div class="col-6">
                    <p class="mb-1"><strong>换算为吨：</strong></p>
                    <h3 class="text-success">${(totalCarbon / 1000).toFixed(4)} tCO₂</h3>
                </div>
            </div>
        </div>
        <div class="row g-3 mt-2">
            <div class="col-md-3">
                <div class="stat-item">
                    <div class="stat-value">${(electricity * factors.electricity).toFixed(2)}</div>
                    <div class="stat-label">电力排放</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-item">
                    <div class="stat-value">${(gas * factors.natural_gas).toFixed(2)}</div>
                    <div class="stat-label">天然气排放</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-item">
                    <div class="stat-value">${(gasoline * factors.gasoline).toFixed(2)}</div>
                    <div class="stat-label">汽油排放</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-item">
                    <div class="stat-value">${(diesel * factors.diesel).toFixed(2)}</div>
                    <div class="stat-label">柴油排放</div>
                </div>
            </div>
        </div>
        <div class="text-center mt-4">
            <button class="btn btn-primary me-2" onclick="openCalculator('esg')">
                <i class="fas fa-chart-bar me-2"></i>查看详细ESG计算
            </button>
            <button class="btn btn-outline-primary" onclick="generateReport('basic')">
                <i class="fas fa-file-alt me-2"></i>生成碳排放报告
            </button>
        </div>
    `;
    
    document.getElementById('quickCalcResult').innerHTML = resultHtml;
}
const PlatformState = {
    user: null,
    theme: 'light',
    currentPage: 'home',
    esgScore: {
        environment: 65,
        social: 70,
        governance: 75,
        total: 70
    },
    carbonData: {},
    reportHistory: [],
    isInitialized: false
};

// 模拟数据服务
const DataService = {
    // 用户管理
    users: [
        { id: 1, email: 'demo@carbon-ai.com', password: 'demo123', name: '演示用户', company: '演示科技有限公司', type: 'ecommerce' }
    ],

    // 行业基准数据
    industryBenchmarks: {
        ecommerce: { carbonPerRevenue: 0.15, energyPerOrder: 0.8, packagingRate: 0.65 },
        manufacture: { carbonPerRevenue: 0.85, energyPerOutput: 1.2, wasteRate: 0.25 },
        logistics: { carbonPerRevenue: 0.45, fuelPerKm: 0.12, efficiencyScore: 0.75 },
        service: { carbonPerRevenue: 0.08, energyPerEmployee: 0.3, digitalRate: 0.9 }
    },

    // 排放因子数据库
    emissionFactors: {
        electricity: 0.581, // kgCO2/kWh (中国电网平均)
        coal: 2.64, // kgCO2/kg
        natural_gas: 1.89, // kgCO2/m³
        gasoline: 2.32, // kgCO2/L
        diesel: 2.68, // kgCO2/L
        water: 0.34, // kgCO2/m³
        waste: 0.85, // kgCO2/kg (填埋)
        recycle: 0.12 // kgCO2/kg (回收)
    },

    // 金融产品数据库
    financialProducts: [
        {
            id: 1,
            name: '绿色信贷优惠包',
            type: 'credit',
            bank: '中国工商银行',
            interestRate: 'LPR-50BP',
            maxAmount: 5000000,
            term: '1-3年',
            requirements: 'ESG评分≥70分',
            description: '专为绿色转型企业设计，利率优惠，审批快速',
            popularity: 95,
            category: 'hot'
        },
        {
            id: 2,
            name: '绿色供应链金融',
            type: 'supplychain',
            bank: '中国建设银行',
            interestRate: '账期延长至90天',
            maxAmount: 3000000,
            term: '按需',
            requirements: '供应链稳定，ESG评分≥75分',
            description: '优化供应链资金流，支持绿色供应链建设',
            popularity: 88,
            category: 'recommended'
        },
        {
            id: 3,
            name: '碳减排项目贷款',
            type: 'project',
            bank: '国家开发银行',
            interestRate: 'LPR-80BP',
            maxAmount: 10000000,
            term: '3-5年',
            requirements: '有明确减排项目，技术可行',
            description: '支持企业节能减排技术改造项目',
            popularity: 92,
            category: 'hot'
        }
    ],

    // 报告模板
    reportTemplates: {
        basic: {
            id: 'basic',
            name: '基础碳核算报告',
            description: '符合国家基本要求的碳核算报告',
            sections: ['企业概况', '核算边界', '排放源识别', '活动数据', '排放量计算', '结果分析'],
            estimatedTime: 15,
            wordCount: 1500,
            charts: 3
        },
        esg: {
            id: 'esg',
            name: 'ESG综合报告',
            description: '环境、社会、治理多维度综合分析报告',
            sections: ['ESG概况', '环境绩效', '社会责任', '公司治理', '风险管理', '改进建议'],
            estimatedTime: 25,
            wordCount: 3000,
            charts: 6
        },
        finance: {
            id: 'finance',
            name: '绿色金融申请报告',
            description: '适配银行绿色信贷申请要求的专业报告',
            sections: ['企业基本信息', '融资需求', '绿色项目介绍', 'ESG表现', '减排效益', '还款保障'],
            estimatedTime: 20,
            wordCount: 2500,
            charts: 4
        }
    },

    // 客户案例数据
    caseStudies: [
        {
            id: 1,
            company: 'A电商公司',
            industry: 'ecommerce',
            challenge: '平台要求绿色商家认证，缺乏碳数据管理能力',
            solution: '使用碳融智核平台进行订单级碳核算，优化包装材料',
            results: {
                carbonReduction: 30,
                costSavings: 150000,
                esgScore: 85,
                timeSaved: 70
            },
            testimonial: '平台帮助我们轻松完成了绿色商家认证，订单量增长了20%'
        },
        {
            id: 2,
            company: 'B制造工厂',
            industry: 'manufacture',
            challenge: '需要申请政府绿色技改补贴，但合规报告编制困难',
            solution: '通过平台自动生成符合要求的ESG报告，精准核算减排量',
            results: {
                subsidyObtained: 1200000,
                esgScore: 82,
                energySaved: 25,
                timeSaved: 85
            },
            testimonial: '成功申请到120万元补贴，平台的专业报告功不可没'
        }
    ],

    // 政策数据
    policies: [
        {
            id: 1,
            title: '双碳目标实施方案',
            agency: '国家发改委',
            date: '2023-06-15',
            summary: '明确2030年前碳达峰、2060年前碳中和的具体实施路径',
            relevance: 'high'
        },
        {
            id: 2,
            title: '中小企业绿色发展指导意见',
            agency: '工信部',
            date: '2023-08-22',
            summary: '支持中小企业绿色转型，提供财税、金融、技术等多方面支持',
            relevance: 'high'
        },
        {
            id: 3,
            title: '绿色信贷指引',
            agency: '中国人民银行',
            date: '2023-11-10',
            summary: '鼓励金融机构加大对绿色项目的信贷支持力度',
            relevance: 'medium'
        }
    ]
};

// ============================================
// 通用工具函数
// ============================================

/**
 * 防抖函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 显示Toast通知
 */
function showToast(message, type = 'info') {
    // 移除已有的toast
    const existingToast = document.querySelector('.custom-toast');
    if (existingToast) {
        existingToast.remove();
    }

    // 创建toast元素
    const toast = document.createElement('div');
    toast.className = `custom-toast alert alert-${type} alert-dismissible fade show`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideInRight 0.3s ease;
    `;
    
    const iconMap = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${iconMap[type] || 'info-circle'} me-2"></i>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // 5秒后自动移除
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

/**
 * 复制文本到剪贴板
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('已复制到剪贴板', 'success');
    }).catch(err => {
        console.error('复制失败:', err);
        showToast('复制失败', 'error');
    });
}

/**
 * 显示模态框
 */
function showModal(title, content, size = 'md') {
    // 移除已有的模态框
    const existingModal = document.getElementById('dynamicModal');
    if (existingModal) {
        existingModal.remove();
    }

    // 创建模态框
    const modal = document.createElement('div');
    modal.id = 'dynamicModal';
    modal.className = 'modal fade';
    modal.tabIndex = '-1';
    
    const modalDialogClass = size === 'lg' ? 'modal-lg' : size === 'xl' ? 'modal-xl' : '';
    
    modal.innerHTML = `
        <div class="modal-dialog ${modalDialogClass}">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // 模态框关闭后移除
    modal.addEventListener('hidden.bs.modal', () => {
        modal.remove();
    });
}

// ============================================
// 初始化函数
// ============================================

/**
 * 平台初始化
 */
function initPlatform() {
    console.log('碳融智核平台初始化...');
    
    // 1. 加载用户数据
    loadUserData();
    
    // 2. 初始化主题
    initTheme();
    
    // 3. 初始化导航
    initNavigation();
    
    // 4. 初始化图表
    initCharts();
    
    // 5. 初始化表单
    initForms();
    
    // 6. 初始化工具
    initTools();
    
    // 7. 初始化事件监听
    initEventListeners();
    
    // 8. 模拟数据加载
    loadSampleData();
    
    // 9. 初始化ESG计算器
    initESGCalculator();
    
    // 标记初始化完成
    PlatformState.isInitialized = true;
    console.log('平台初始化完成！');
    
    // 显示欢迎消息
    showWelcomeMessage();
}

/**
 * 加载用户数据
 */
function loadUserData() {
    try {
        const savedUser = localStorage.getItem(CONFIG.USER_KEY);
        if (savedUser) {
            PlatformState.user = JSON.parse(savedUser);
            updateUserUI();
        }
        
        const savedData = localStorage.getItem(CONFIG.LOCAL_STORAGE_KEY);
        if (savedData) {
            const data = JSON.parse(savedData);
            PlatformState.esgScore = data.esgScore || PlatformState.esgScore;
            PlatformState.carbonData = data.carbonData || PlatformState.carbonData;
            PlatformState.reportHistory = data.reportHistory || PlatformState.reportHistory;
        }
    } catch (error) {
        console.error('加载用户数据失败:', error);
    }
}

/**
 * 保存用户数据
 */
function saveUserData() {
    try {
        if (PlatformState.user) {
            localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(PlatformState.user));
        }
        
        const data = {
            esgScore: PlatformState.esgScore,
            carbonData: PlatformState.carbonData,
            reportHistory: PlatformState.reportHistory,
            lastUpdated: new Date().toISOString()
        };
        
        localStorage.setItem(CONFIG.LOCAL_STORAGE_KEY, JSON.stringify(data));
    } catch (error) {
        console.error('保存用户数据失败:', error);
    }
}

/**
 * 初始化主题
 */
function initTheme() {
    const savedTheme = localStorage.getItem(CONFIG.THEME_KEY) || 'light';
    PlatformState.theme = savedTheme;
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // 更新主题切换按钮
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.innerHTML = savedTheme === 'dark' ? 
            '<i class="fas fa-sun"></i>' : 
            '<i class="fas fa-moon"></i>';
    }
}

/**
 * 切换主题
 */
function toggleTheme() {
    const newTheme = PlatformState.theme === 'light' ? 'dark' : 'light';
    PlatformState.theme = newTheme;
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem(CONFIG.THEME_KEY, newTheme);
    
    // 更新按钮图标
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.innerHTML = newTheme === 'dark' ? 
            '<i class="fas fa-sun"></i>' : 
            '<i class="fas fa-moon"></i>';
    }
    
    // 显示切换提示
    showToast(`已切换至${newTheme === 'dark' ? '深色' : '浅色'}主题`, 'success');
}

/**
 * 更新用户界面
 */
function updateUserUI() {
    if (!PlatformState.user) return;
    
    // 更新登录按钮
    const loginBtn = document.querySelector('[data-bs-target="#loginModal"]');
    if (loginBtn) {
        loginBtn.innerHTML = `<i class="fas fa-user me-1"></i>${PlatformState.user.name}`;
        loginBtn.classList.remove('btn-success');
        loginBtn.classList.add('btn-outline-light');
    }
    
    // 显示欢迎消息
    const userWelcome = document.getElementById('userWelcome');
    if (userWelcome) {
        userWelcome.textContent = `欢迎回来，${PlatformState.user.name}！`;
        userWelcome.style.display = 'block';
    }
}

// ============================================
// 导航和滚动功能
// ============================================

/**
 * 初始化导航
 */
function initNavigation() {
    // 平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                
                // 更新导航状态
                updateNavActiveState(href);
                
                // 平滑滚动
                window.scrollTo({
                    top: target.offsetTop - 80,
                    behavior: 'smooth'
                });
                
                // 更新页面状态
                PlatformState.currentPage = href.substring(1);
            }
        });
    });
    
    // 滚动时更新导航
    window.addEventListener('scroll', debounce(() => {
        updateNavOnScroll();
        updateBackToTopButton();
    }, 100));
}

/**
 * 更新导航激活状态
 */
function updateNavActiveState(targetId) {
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === targetId) {
            link.classList.add('active');
        }
    });
}

/**
 * 滚动时更新导航
 */
function updateNavOnScroll() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    let current = '';
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop - 100;
        if (window.scrollY >= sectionTop) {
            current = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${current}`) {
            link.classList.add('active');
        }
    });
    
    // 更新导航栏样式
    const navbar = document.getElementById('mainNavbar');
    if (navbar) {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
}

/**
 * 更新返回顶部按钮
 */
function updateBackToTopButton() {
    const btn = document.getElementById('scrollTopBtn');
    if (btn) {
        if (window.scrollY > 300) {
            btn.style.display = 'flex';
        } else {
            btn.style.display = 'none';
        }
    }
}

// ============================================
// 图表初始化
// ============================================

/**
 * 初始化图表
 */
function initCharts() {
    // 首页仪表板
    initHeroDashboard();
    
    // 功能演示仪表板
    initDashboardDemo();
    
    // ESG雷达图
    initESGRadarChart();
    
    // 统计数字动画
    initCounterAnimation();
}

/**
 * 初始化首页仪表板
 */
function initHeroDashboard() {
    const chartDom = document.getElementById('heroDashboard');
    if (!chartDom) return;
    
    const chart = echarts.init(chartDom);
    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#2E7D32',
            borderWidth: 1,
            textStyle: {
                color: '#333'
            }
        },
        legend: {
            data: ['碳排放量', '能耗', 'ESG评分'],
            textStyle: {
                color: 'rgba(255, 255, 255, 0.9)'
            },
            top: 10
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '20%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月'],
            axisLine: {
                lineStyle: {
                    color: 'rgba(255, 255, 255, 0.5)'
                }
            },
            axisLabel: {
                color: 'rgba(255, 255, 255, 0.8)'
            }
        },
        yAxis: {
            type: 'value',
            axisLine: {
                lineStyle: {
                    color: 'rgba(255, 255, 255, 0.5)'
                }
            },
            axisLabel: {
                color: 'rgba(255, 255, 255, 0.8)'
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255, 255, 255, 0.1)'
                }
            }
        },
        series: [
            {
                name: '碳排放量',
                type: 'line',
                smooth: true,
                data: [120, 132, 101, 134, 90, 230, 210],
                lineStyle: {
                    width: 3,
                    color: '#4CAF50'
                },
                itemStyle: {
                    color: '#4CAF50'
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(76, 175, 80, 0.3)' },
                        { offset: 1, color: 'rgba(76, 175, 80, 0.1)' }
                    ])
                }
            },
            {
                name: '能耗',
                type: 'line',
                smooth: true,
                data: [220, 182, 191, 234, 290, 330, 310],
                lineStyle: {
                    width: 3,
                    color: '#FF9800'
                },
                itemStyle: {
                    color: '#FF9800'
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(255, 152, 0, 0.3)' },
                        { offset: 1, color: 'rgba(255, 152, 0, 0.1)' }
                    ])
                }
            },
            {
                name: 'ESG评分',
                type: 'line',
                smooth: true,
                data: [65, 72, 75, 78, 82, 85, 88],
                lineStyle: {
                    width: 3,
                    color: '#0288D1'
                },
                itemStyle: {
                    color: '#0288D1'
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(2, 136, 209, 0.3)' },
                        { offset: 1, color: 'rgba(2, 136, 209, 0.1)' }
                    ])
                }
            }
        ]
    };
    
    chart.setOption(option);
    
    // 响应式调整
    window.addEventListener('resize', () => {
        chart.resize();
    });
}

/**
 * 初始化功能演示仪表板
 */
function initDashboardDemo() {
    const chartDom = document.getElementById('dashboardDemo');
    if (!chartDom) return;
    
    const chart = echarts.init(chartDom);
    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                crossStyle: {
                    color: '#999'
                }
            }
        },
        toolbox: {
            feature: {
                dataView: { show: true, readOnly: false },
                magicType: { show: true, type: ['line', 'bar'] },
                restore: { show: true },
                saveAsImage: { show: true }
            }
        },
        legend: {
            data: ['碳排放强度', '行业平均', '优秀水平'],
            top: 10
        },
        xAxis: [
            {
                type: 'category',
                data: ['电商', '制造', '物流', '服务', '零售', '建筑'],
                axisPointer: {
                    type: 'shadow'
                }
            }
        ],
        yAxis: [
            {
                type: 'value',
                name: '碳排放强度',
                min: 0,
                max: 1.5,
                interval: 0.3,
                axisLabel: {
                    formatter: '{value} t/万元'
                }
            }
        ],
        series: [
            {
                name: '碳排放强度',
                type: 'bar',
                data: [0.15, 0.85, 0.45, 0.08, 0.25, 0.95],
                itemStyle: {
                    color: '#4CAF50'
                },
                barWidth: '40%'
            },
            {
                name: '行业平均',
                type: 'line',
                data: [0.18, 0.92, 0.52, 0.12, 0.30, 1.05],
                itemStyle: {
                    color: '#FF9800'
                },
                lineStyle: {
                    width: 3,
                    type: 'dashed'
                }
            },
            {
                name: '优秀水平',
                type: 'line',
                data: [0.10, 0.65, 0.35, 0.05, 0.18, 0.75],
                itemStyle: {
                    color: '#0288D1'
                },
                lineStyle: {
                    width: 3
                }
            }
        ]
    };
    
    chart.setOption(option);
    
    // 响应式调整
    window.addEventListener('resize', () => {
        chart.resize();
    });
}

/**
 * 初始化ESG雷达图
 */
function initESGRadarChart() {
    const chartDom = document.getElementById('esgRadarChart');
    if (!chartDom) return;
    
    const chart = echarts.init(chartDom);
    const option = {
        tooltip: {
            trigger: 'item'
        },
        radar: {
            indicator: [
                { name: '碳管理', max: 100 },
                { name: '能耗效率', max: 100 },
                { name: '废弃物管理', max: 100 },
                { name: '员工福祉', max: 100 },
                { name: '供应链责任', max: 100 },
                { name: '信息披露', max: 100 }
            ],
            shape: 'circle',
            splitNumber: 5,
            axisName: {
                color: '#333',
                fontSize: 12
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            },
            splitArea: {
                show: true,
                areaStyle: {
                    color: ['rgba(255, 255, 255, 0.8)', 'rgba(200, 200, 200, 0.1)']
                }
            }
        },
        series: [
            {
                type: 'radar',
                data: [
                    {
                        value: [75, 80, 65, 85, 70, 90],
                        name: '当前表现',
                        itemStyle: {
                            color: '#4CAF50'
                        },
                        areaStyle: {
                            color: 'rgba(76, 175, 80, 0.3)'
                        },
                        lineStyle: {
                            width: 2
                        }
                    },
                    {
                        value: [60, 65, 55, 70, 60, 75],
                        name: '行业平均',
                        itemStyle: {
                            color: '#FF9800'
                        },
                        areaStyle: {
                            color: 'rgba(255, 152, 0, 0.1)'
                        },
                        lineStyle: {
                            type: 'dashed',
                            width: 1
                        }
                    }
                ]
            }
        ]
    };
    
    chart.setOption(option);
    
    // 响应式调整
    window.addEventListener('resize', () => {
        chart.resize();
    });
}

/**
 * 初始化统计数字动画
 */
function initCounterAnimation() {
    const counters = document.querySelectorAll('.stat-value[data-count]');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.getAttribute('data-count'));
                const suffix = counter.getAttribute('data-suffix') || '';
                animateCounter(counter, target, suffix);
                observer.unobserve(counter);
            }
        });
    }, { threshold: 0.5 });
    
    counters.forEach(counter => {
        observer.observe(counter);
    });
}

/**
 * 数字动画效果
 */
function animateCounter(element, target, suffix = '') {
    let current = 0;
    const increment = target / 100;
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current) + suffix;
    }, 20);
}

// ============================================
// 表单初始化
// ============================================

/**
 * 初始化表单
 */
function initForms() {
    // 登录表单
    initLoginForm();
    
    // 注册表单
    initRegisterForm();
    
    // 联系表单
    initContactForm();
    
    // OCR演示表单
    initOCRDemo();
    
    // 报告生成表单
    initReportGenerator();
}

/**
 * 初始化登录表单
 */
function initLoginForm() {
    const loginForm = document.getElementById('loginFormContent');
    if (!loginForm) return;
    
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = loginForm.querySelector('input[type="email"]').value;
        const password = loginForm.querySelector('input[type="password"]').value;
        const loginBtn = loginForm.querySelector('button[type="submit"]');
        const originalText = loginBtn.innerHTML;
        
        loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>登录中...';
        loginBtn.disabled = true;
        
        // 调用后端API登录
        API.login(email, password).then(data => {
            localStorage.setItem('carbon_platform_logged_in', 'true');
            PlatformState.user = {
                id: data.user.id,
                email: data.user.email,
                name: data.user.name,
                company: data.user.company || '',
                type: data.user.company_type || 'ecommerce',
                loginTime: new Date().toISOString()
            };
            saveUserData();
            updateUserUI();
            const modal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
            if (modal) modal.hide();
            checkLoginStatus();
            showToast(`欢迎回来，${data.user.name}！`, 'success');
        }).catch(err => {
            showToast(err.message || '邮箱或密码错误，请重试', 'error');
        }).finally(() => {
            loginBtn.innerHTML = originalText;
            loginBtn.disabled = false;
            loginForm.reset();
        });
    });
    
    // 登录标签切换
    const loginTabs = document.querySelectorAll('.login-tab');
    loginTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.getAttribute('data-tab');
            
            // 更新标签状态
            loginTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // 显示对应内容
            document.querySelectorAll('.login-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabName}Form`).classList.add('active');
        });
    });
}

/**
 * 初始化注册表单
 */
function initRegisterForm() {
    const registerForm = document.getElementById('registerFormContent');
    if (!registerForm) return;
    
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = registerForm.querySelector('input[type="text"]').value;
        const company = registerForm.querySelectorAll('input[type="text"]')[1].value;
        const email = registerForm.querySelector('input[type="email"]').value;
        const password = registerForm.querySelectorAll('input[type="password"]')[0].value;
        const confirmPassword = registerForm.querySelectorAll('input[type="password"]')[1].value;
        
        if (password !== confirmPassword) {
            showToast('两次输入的密码不一致', 'error');
            return;
        }
        
        const registerBtn = registerForm.querySelector('button[type="submit"]');
        const originalText = registerBtn.innerHTML;
        
        registerBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>注册中...';
        registerBtn.disabled = true;
        
        // 调用后端API注册
        API.register({ name, company, email, password }).then(data => {
            localStorage.setItem('carbon_platform_logged_in', 'true');
            PlatformState.user = {
                id: data.user.id,
                email: data.user.email,
                name: data.user.name,
                company: data.user.company || '',
                type: data.user.company_type || 'ecommerce',
                loginTime: new Date().toISOString()
            };
            saveUserData();
            updateUserUI();
            const modal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
            if (modal) modal.hide();
            checkLoginStatus();
            showToast(`注册成功！欢迎加入碳融智核，${data.user.name}！`, 'success');
        }).catch(err => {
            showToast(err.message || '注册失败，请重试', 'error');
        }).finally(() => {
            registerBtn.innerHTML = originalText;
            registerBtn.disabled = false;
            registerForm.reset();
        });
    });
}

/**
 * 初始化联系表单
 */
function initContactForm() {
    const contactForm = document.getElementById('contactForm');
    if (!contactForm) return;
    
    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = contactForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>提交中...';
        submitBtn.disabled = true;
        
        // 调用后端API提交联系表单
        const formData = {
            name: contactForm.querySelector('[name="contact_name"], input[placeholder*="姓名"]')?.value || '',
            company: contactForm.querySelector('[name="contact_company"], input[placeholder*="企业"]')?.value || '',
            phone: contactForm.querySelector('[name="contact_phone"], input[type="tel"]')?.value || '',
            email: contactForm.querySelector('[name="contact_email"], input[type="email"]')?.value || '',
            message: contactForm.querySelector('[name="message"], textarea')?.value || '',
            company_type: contactForm.querySelector('[name="company_type"], select')?.value || ''
        };
        API.submitContact(formData).then(() => {
            showToast('咨询提交成功！我们的客服将在24小时内联系您。', 'success');
            contactForm.reset();
            const modal = bootstrap.Modal.getInstance(document.getElementById('contactModal'));
            if (modal) modal.hide();
        }).catch(err => {
            showToast(err.message || '提交失败，请稍后重试', 'error');
        }).finally(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
    });
}

// ============================================
// OCR演示功能
// ============================================

/**
 * 初始化OCR演示
 */
function initOCRDemo() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput) return;
    
    fileInput.addEventListener('change', handleFileUpload);
    
    // 拖放功能
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#2E7D32';
            uploadArea.style.backgroundColor = '#E8F5E9';
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = '';
            uploadArea.style.backgroundColor = '';
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '';
            uploadArea.style.backgroundColor = '';
            if (e.dataTransfer.files.length) {
                handleFileUpload({ target: { files: e.dataTransfer.files } });
            }
        });
    }
}

/**
 * 处理文件上传
 */
function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const uploadArea = document.getElementById('uploadArea');
    const ocrResult = document.getElementById('ocrResult');
    if (!uploadArea || !ocrResult) return;
    
    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
        showToast('请上传图片文件 (JPEG, PNG) 或 PDF 文件', 'error');
        return;
    }
    
    // 验证文件大小
    if (file.size > 10 * 1024 * 1024) {
        showToast('文件太大，请上传小于10MB的文件', 'error');
        return;
    }
    
    // 显示上传状态
    uploadArea.innerHTML = `
        <i class="fas fa-spinner fa-spin fa-3x text-primary"></i>
        <p class="mt-3">正在上传文件...</p>
        <div class="progress mt-3">
            <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%"></div>
        </div>
    `;
    
    // 模拟OCR处理
    setTimeout(() => {
        const sampleResults = {
            electricity: {
                title: '电费单识别结果',
                data: {
                    '用电类型': '工商业用电',
                    '用电量': '1,245 kWh',
                    '电费金额': '¥ 1,245.00',
                    '计费期间': '2024年3月1日-3月31日',
                    '识别准确率': '98.5%'
                }
            },
            logistics: {
                title: '物流面单识别结果',
                data: {
                    '运单号': 'SF1234567890',
                    '收件人': '张先生',
                    '重量': '2.5 kg',
                    '运输距离': '350 km',
                    '运输方式': '陆运',
                    '识别准确率': '96.2%'
                }
            },
            fuel: {
                title: '加油发票识别结果',
                data: {
                    '油品类型': '95#汽油',
                    '加油量': '45.6 L',
                    '金额': '¥ 386.52',
                    '加油站': '中国石化',
                    '识别准确率': '97.8%'
                }
            }
        };
        
        // 根据文件名猜测类型
        let sampleType = 'electricity';
        const fileName = file.name.toLowerCase();
        if (fileName.includes('物流') || fileName.includes('快递')) {
            sampleType = 'logistics';
        } else if (fileName.includes('油') || fileName.includes('fuel')) {
            sampleType = 'fuel';
        }
        
        const result = sampleResults[sampleType];
        
        // 显示识别结果
        ocrResult.innerHTML = `
            <div class="result-content">
                <h5><i class="fas fa-check-circle text-success me-2"></i>${result.title}</h5>
                <div class="result-details mt-3">
                    ${Object.entries(result.data).map(([key, value]) => `
                        <div class="result-item">
                            <span class="result-key">${key}：</span>
                            <span class="result-value">${value}</span>
                        </div>
                    `).join('')}
                </div>
                <div class="result-actions mt-4">
                    <button class="btn btn-sm btn-success me-2" onclick="useOCRData('${sampleType}')">
                        <i class="fas fa-check me-1"></i>使用此数据
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="resetOCRDemo()">
                        <i class="fas fa-redo me-1"></i>重新识别
                    </button>
                </div>
            </div>
        `;
        
        // 重置上传区域
        uploadArea.innerHTML = `
            <i class="fas fa-check-circle fa-3x text-success"></i>
            <p class="mt-3">${file.name}</p>
            <p class="text-muted small">文件上传成功</p>
            <button class="btn btn-outline-primary mt-3" onclick="document.getElementById('fileInput').click()">
                选择其他文件
            </button>
        `;
        
        showToast('OCR识别完成！', 'success');
    }, 2000);
}

/**
 * 使用OCR数据
 */
function useOCRData(type) {
    const sampleData = {
        electricity: {
            electricityUsage: 1245,
            electricityCost: 1245
        },
        logistics: {
            logisticsDistance: 350,
            logisticsWeight: 2.5
        },
        fuel: {
            fuelUsage: 45.6,
            fuelCost: 386.52
        }
    };
    
    const data = sampleData[type];
    if (!data) return;
    
    // 填充到ESG计算器
    if (data.electricityUsage) {
        const electricityInput = document.getElementById('electricityUsage');
        if (electricityInput) electricityInput.value = data.electricityUsage;
    }
    
    if (data.fuelUsage) {
        const fuelInput = document.getElementById('fuelUsage');
        if (fuelInput) fuelInput.value = data.fuelUsage;
    }
    
    showToast('OCR数据已自动填充到计算器中！', 'success');
    
    // 关闭OCR模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('ocrDemoModal'));
    if (modal) modal.hide();
    
    // 自动计算
    setTimeout(() => calculateEnvironmental(), 500);
}

/**
 * 重置OCR演示
 */
function resetOCRDemo() {
    const uploadArea = document.getElementById('uploadArea');
    const ocrResult = document.getElementById('ocrResult');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadArea) {
        uploadArea.innerHTML = `
            <i class="fas fa-cloud-upload-alt fa-3x text-muted"></i>
            <p class="mt-3">拖拽文件到这里，或点击选择文件</p>
            <p class="text-muted small">支持 JPG, PNG, PDF 格式，最大10MB</p>
            <input type="file" id="fileInput" class="d-none" accept=".jpg,.jpeg,.png,.pdf" onchange="handleFileUpload(event)">
            <button class="btn btn-outline-primary mt-3" onclick="document.getElementById('fileInput').click()">
                选择文件
            </button>
        `;
    }
    
    if (ocrResult) {
        ocrResult.innerHTML = `
            <div class="result-placeholder">
                <i class="fas fa-search fa-2x text-muted"></i>
                <p class="mt-3">识别结果将显示在这里</p>
            </div>
        `;
    }
    
    if (fileInput) {
        fileInput.value = '';
    }
}

/**
 * 加载示例文件
 */
function loadSample(type) {
    const sampleFiles = {
        electricity: '电费单示例.jpg',
        logistics: '物流面单示例.jpg',
        fuel: '加油发票示例.jpg'
    };
    
    const fileName = sampleFiles[type];
    if (!fileName) return;
    
    showToast(`正在加载${fileName}...`, 'info');
    
    // 模拟文件加载
    setTimeout(() => {
        const event = {
            target: {
                files: [{
                    name: fileName,
                    size: 1024 * 1024 * 2, // 2MB
                    type: 'image/jpeg'
                }]
            }
        };
        handleFileUpload(event);
    }, 1000);
}

// ============================================
// 报告生成功能
// ============================================

/**
 * 初始化报告生成器
 */
function initReportGenerator() {
    // 报告类型选择
    const reportTypeCards = document.querySelectorAll('.report-type-card');
    reportTypeCards.forEach(card => {
        card.addEventListener('click', () => {
            const type = card.getAttribute('data-type');
            
            // 更新卡片状态
            reportTypeCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            
            // 更新报告生成器
            updateReportGenerator(type);
        });
    });
    
    // 模板选择
    const templateButtons = document.querySelectorAll('[onclick*="generateReport"]');
    templateButtons.forEach(button => {
        const originalOnclick = button.getAttribute('onclick');
        button.removeAttribute('onclick');
        button.addEventListener('click', () => {
            const match = originalOnclick.match(/generateReport\('(\w+)'\)/);
            if (match) {
                generateReport(match[1]);
            }
        });
    });
}

/**
 * 更新报告生成器
 */
function updateReportGenerator(type) {
    const preview = document.getElementById('reportPreview');
    if (!preview) return;
    
    const templates = {
        carbon: {
            title: '碳排放报告',
            description: '企业年度碳排放核算与分析报告',
            sections: ['核算边界', '排放源识别', '活动数据', '排放量计算', '结果分析', '改进建议']
        },
        esg: {
            title: 'ESG综合报告',
            description: '环境、社会、治理全方位评估报告',
            sections: ['ESG概况', '环境绩效', '社会责任', '公司治理', '风险管理', '未来发展']
        },
        finance: {
            title: '绿色金融报告',
            description: '绿色信贷申请与融资评估报告',
            sections: ['企业概况', '融资需求', '绿色项目', 'ESG表现', '减排效益', '还款保障']
        },
        supplychain: {
            title: '供应链碳足迹报告',
            description: '供应链碳排放分析与优化建议',
            sections: ['供应链概况', '碳足迹计算', '热点分析', '优化方案', '实施计划', '预期效益']
        }
    };
    
    const template = templates[type] || templates.carbon;
    
    preview.innerHTML = `
        <div class="preview-content">
            <h5><i class="fas fa-file-alt me-2"></i>${template.title}</h5>
            <p class="text-muted">${template.description}</p>
            <div class="preview-sections mt-4">
                <h6>报告章节：</h6>
                <ul class="mt-2">
                    ${template.sections.map(section => `
                        <li><i class="fas fa-check-circle text-success me-2"></i>${section}</li>
                    `).join('')}
                </ul>
            </div>
            <div class="preview-stats mt-4">
                <div class="row">
                    <div class="col-4">
                        <div class="stat">
                            <div class="stat-value">${template.sections.length}</div>
                            <div class="stat-label">章节数</div>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="stat">
                            <div class="stat-value">15-20</div>
                            <div class="stat-label">预估页数</div>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="stat">
                            <div class="stat-value">5-8</div>
                            <div class="stat-label">图表数量</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * 生成报告
 */
function generateReport(templateType) {
    const template = DataService.reportTemplates[templateType];
    if (!template) return;
    
    const reportPreview = document.getElementById('reportPreview');
    if (!reportPreview) return;
    
    reportPreview.innerHTML = `
        <div class="report-generating">
            <div class="text-center">
                <i class="fas fa-robot fa-3x text-warning mb-3"></i>
                <h5>AIGC正在生成报告...</h5>
                <p class="text-muted">请稍候，这可能需要几分钟时间</p>
                <div class="progress mt-4" style="height: 8px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%"></div>
                </div>
                <div class="generating-details mt-4">
                    <div class="row">
                        <div class="col-6">
                            <small class="text-muted">报告模板</small>
                            <p class="mb-0">${template.name}</p>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">预估时间</small>
                            <p class="mb-0">${template.estimatedTime}秒</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 调用后端API生成报告
    API.generateReport({
        template_type: templateType,
        title: `${template.name} - ${new Date().toLocaleDateString()}`
    }).then(report => {
        const reportId = report.report_no || ('REPORT-' + Date.now().toString().slice(-8));
        const generationTime = report.generation_time || template.estimatedTime;
        // 保存到本地历史
        PlatformState.reportHistory.unshift({
            id: reportId,
            dbId: report.id,
            template: templateType,
            name: report.title || `${template.name} - ${new Date().toLocaleDateString()}`,
            generatedAt: report.created_at || new Date().toISOString(),
            generationTime: generationTime,
            wordCount: report.word_count || template.wordCount,
            charts: report.charts_count || template.charts,
            status: 'completed'
        });
        saveUserData();
        
        // 显示报告结果
        reportPreview.innerHTML = `
            <div class="report-completed">
                <div class="text-center mb-4">
                    <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
                    <h5>报告生成完成！</h5>
                    <p class="text-muted">${template.name}已成功生成</p>
                </div>
                <div class="report-details">
                    <div class="row mb-3">
                        <div class="col-6">
                            <small class="text-muted">报告编号</small>
                            <p class="mb-0"><strong>${reportId}</strong></p>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">生成时间</small>
                            <p class="mb-0">${generationTime}秒</p>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-6">
                            <small class="text-muted">总字数</small>
                            <p class="mb-0">${report.wordCount}字</p>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">图表数量</small>
                            <p class="mb-0">${report.charts}个</p>
                        </div>
                    </div>
                    <div class="report-sections mb-4">
                        <small class="text-muted d-block mb-2">包含章节：</small>
                        <div class="d-flex flex-wrap gap-1">
                            ${template.sections.map(section => `
                                <span class="badge bg-light text-dark">${section}</span>
                            `).join('')}
                        </div>
                    </div>
                </div>
                <div class="report-actions">
                    <button class="btn btn-success w-100 mb-2" onclick="downloadReport('${reportId}')">
                        <i class="fas fa-download me-2"></i>下载报告 (PDF)
                    </button>
                    <button class="btn btn-outline-primary w-100 mb-2" onclick="shareReport('${reportId}')">
                        <i class="fas fa-share-alt me-2"></i>分享报告
                    </button>
                    <button class="btn btn-outline-secondary w-100" onclick="viewReportHistory()">
                        <i class="fas fa-history me-2"></i>查看历史报告
                    </button>
                </div>
            </div>
        `;
        
        showToast(`报告生成完成！编号: ${reportId}`, 'success');
    }).catch(err => {
        if (reportPreview) reportPreview.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-circle me-2"></i>${err.message || '报告生成失败，请稍后重试'}</div>`;
        showToast(err.message || '报告生成失败', 'error');
    });
}

/**
 * 下载报告
 */
function downloadReport(reportId) {
    showToast('正在生成PDF文件，请稍候...', 'info');
    
    setTimeout(() => {
        // 创建模拟下载
        const link = document.createElement('a');
        link.href = `data:application/pdf;base64,${btoa('模拟PDF文件内容')}`;
        link.download = `碳融智核报告_${reportId}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showToast('PDF文件下载完成！', 'success');
    }, 2000);
}

/**
 * 分享报告
 */
function shareReport(reportId) {
    const shareUrl = `${window.location.origin}/report/${reportId}`;
    const shareText = `查看我的碳融智核报告: ${reportId}`;
    
    if (navigator.share) {
        navigator.share({
            title: '碳融智核报告',
            text: shareText,
            url: shareUrl
        }).then(() => {
            showToast('报告分享成功！', 'success');
        }).catch(err => {
            console.error('分享失败:', err);
            copyToClipboard(shareUrl);
        });
    } else {
        copyToClipboard(shareUrl);
    }
}

/**
 * 保存报告至云端
 */
function saveToCloud(reportId) {
    // 从历史中找到最新的报告
    const dbId = reportId || (PlatformState.reportHistory.length > 0 ? PlatformState.reportHistory[0].dbId : null);
    if (!dbId) {
        showToast('请先生成报告再保存到云端', 'warning');
        return;
    }
    API.post(`/reports/${dbId}/save-cloud`, {}).then(data => {
        showToast(data.message || '报告已保存至云端', 'success');
    }).catch(err => {
        showToast(err.message || '保存失败，请确保已登录', 'error');
    });
}

/**
 * 查看报告历史
 */
function viewReportHistory() {
    if (!PlatformState.reportHistory.length) {
        showToast('暂无报告历史', 'info');
        return;
    }
    
    const historyHtml = PlatformState.reportHistory.map(report => `
        <div class="history-item">
            <div class="d-flex justify-content-between">
                <div>
                    <h6 class="mb-1">${report.name}</h6>
                    <small class="text-muted">${new Date(report.generatedAt).toLocaleString()}</small>
                </div>
                <div class="text-end">
                    <small class="text-muted d-block">${report.generationTime}秒</small>
                    <span class="badge bg-success">已完成</span>
                </div>
            </div>
        </div>
    `).join('');
    
    showModal('报告历史', `
        <div class="report-history">
            ${PlatformState.reportHistory.length ? historyHtml : '<p class="text-muted text-center">暂无报告历史</p>'}
        </div>
    `);
}

// ============================================
// ESG计算器功能
// ============================================

/**
 * 计算环境绩效分数
 */
function calculateEnvironmental() {
    const companyType = document.getElementById('companyType').value;
    const annualRevenue = parseFloat(document.getElementById('annualRevenue').value) || 1000;
    const electricityUsage = parseFloat(document.getElementById('electricityUsage').value) || 0;
    const gasUsage = parseFloat(document.getElementById('gasUsage').value) || 0;
    const fuelUsage = parseFloat(document.getElementById('fuelUsage').value) || 0;
    const wasteGeneration = parseFloat(document.getElementById('wasteGeneration').value) || 0;
    const recyclingRate = parseFloat(document.getElementById('recyclingRate').value) || 0;
    
    // 获取排放因子
    const factors = DataService.emissionFactors;
    
    // 计算碳排放
    const carbonEmission = 
        (electricityUsage * factors.electricity) +
        (gasUsage * factors.natural_gas) +
        (fuelUsage * factors.diesel);
    
    // 计算碳强度（吨CO2/万元营收）
    const carbonIntensity = carbonEmission / (annualRevenue * 10000);
    
    // 获取行业基准
    const benchmark = DataService.industryBenchmarks[companyType] || 
                     DataService.industryBenchmarks.manufacture;
    
    // 计算环境分数（基于行业比较）
    let envScore = 0;
    
    // 1. 碳强度比较（40%权重）
    const industryCarbonIntensity = benchmark.carbonPerRevenue || 0.5;
    const carbonScore = Math.max(0, 100 - (carbonIntensity / industryCarbonIntensity) * 100);
    envScore += carbonScore * 0.4;
    
    // 2. 能源效率（30%权重）
    const energyPerRevenue = (electricityUsage + gasUsage * 10 + fuelUsage * 10) / annualRevenue;
    const energyBenchmark = benchmark.energyPerOrder || 1;
    const energyScore = Math.max(0, 100 - (energyPerRevenue / energyBenchmark) * 50);
    envScore += energyScore * 0.3;
    
    // 3. 废弃物管理（20%权重）
    const wasteScore = recyclingRate;
    envScore += wasteScore * 0.2;
    
    // 4. 使用清洁能源加分（10%权重）
    const cleanEnergyScore = electricityUsage > 0 ? 20 : 0; // 如果有电力使用，假设部分清洁
    envScore += cleanEnergyScore * 0.1;
    
    // 限制分数在0-100之间
    envScore = Math.min(100, Math.max(0, Math.round(envScore)));
    
    // 更新全局状态
    PlatformState.esgScore.environment = envScore;
    updateESGVisualization();
    
    // 显示结果
    const resultHtml = `
        <div class="result-content">
            <h5><i class="fas fa-leaf text-success me-2"></i>环境绩效计算结果</h5>
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="result-item">
                        <span class="result-label">总碳排放量：</span>
                        <span class="result-value">${carbonEmission.toFixed(2)} kgCO2</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">碳强度：</span>
                        <span class="result-value">${carbonIntensity.toFixed(4)} t/万元</span>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="result-item">
                        <span class="result-label">行业基准：</span>
                        <span class="result-value">${industryCarbonIntensity.toFixed(4)} t/万元</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">废弃物回收率：</span>
                        <span class="result-value">${recyclingRate}%</span>
                    </div>
                </div>
            </div>
            <div class="alert ${envScore >= 70 ? 'alert-success' : envScore >= 50 ? 'alert-warning' : 'alert-danger'} mt-3">
                <i class="fas fa-chart-line me-2"></i>
                <strong>环境(E)得分：${envScore}分</strong> - 
                ${envScore >= 80 ? '优秀水平，远低于行业平均' : 
                  envScore >= 60 ? '良好水平，接近行业平均' : 
                  '待改进水平，建议优化能源结构'}
            </div>
        </div>
    `;
    
    document.getElementById('calcResult').innerHTML = resultHtml;
    showToast('环境绩效计算完成！', 'success');
}

/**
 * 计算社会责任分数
 */
function calculateSocial() {
    const employeeScale = document.getElementById('employeeScale').value;
    const employeeSatisfaction = parseFloat(document.getElementById('employeeSatisfaction').value) || 75;
    const trainingHours = parseFloat(document.getElementById('trainingHours').value) || 20;
    const turnoverRate = parseFloat(document.getElementById('turnoverRate').value) || 15;
    const communityInvestment = parseFloat(document.getElementById('communityInvestment').value) || 50;
    const supplierESG = parseFloat(document.getElementById('supplierESG').value) || 60;
    const customerSatisfaction = parseFloat(document.getElementById('customerSatisfaction').value) || 85;
    const complaintRate = parseFloat(document.getElementById('complaintRate').value) || 2;
    
    let socialScore = 0;
    
    // 1. 员工权益与福利（40%权重）
    // - 员工满意度（15%）
    const satisfactionScore = employeeSatisfaction;
    socialScore += satisfactionScore * 0.15;
    
    // - 培训发展（15%）
    let trainingScore = 0;
    if (trainingHours >= 40) trainingScore = 100;
    else if (trainingHours >= 30) trainingScore = 80;
    else if (trainingHours >= 20) trainingScore = 60;
    else if (trainingHours >= 10) trainingScore = 40;
    else trainingScore = 20;
    socialScore += trainingScore * 0.15;
    
    // - 员工流失率（10%）
    let turnoverScore = 0;
    if (turnoverRate <= 5) turnoverScore = 100;
    else if (turnoverRate <= 10) turnoverScore = 80;
    else if (turnoverRate <= 15) turnoverScore = 60;
    else if (turnoverRate <= 20) turnoverScore = 40;
    else turnoverScore = 20;
    socialScore += turnoverScore * 0.10;
    
    // 2. 社区投入与责任（20%权重）
    // - 社区投资（10%）
    let communityScore = 0;
    if (communityInvestment >= 100) communityScore = 100;
    else if (communityInvestment >= 50) communityScore = 80;
    else if (communityInvestment >= 20) communityScore = 60;
    else if (communityInvestment >= 10) communityScore = 40;
    else communityScore = 20;
    socialScore += communityScore * 0.10;
    
    // - 供应链责任（10%）
    socialScore += supplierESG * 0.10;
    
    // 3. 客户与消费者权益（40%权重）
    // - 客户满意度（25%）
    const customerScore = customerSatisfaction;
    socialScore += customerScore * 0.25;
    
    // - 产品服务质量（15%）
    let complaintScore = 0;
    if (complaintRate <= 1) complaintScore = 100;
    else if (complaintRate <= 3) complaintScore = 80;
    else if (complaintRate <= 5) complaintScore = 60;
    else if (complaintRate <= 10) complaintScore = 40;
    else complaintScore = 20;
    socialScore += complaintScore * 0.15;
    
    // 4. 根据企业规模调整
    if (employeeScale === 'small') {
        socialScore *= 1.1; // 小型企业加分
    } else if (employeeScale === 'large') {
        socialScore *= 0.95; // 大型企业要求更高
    }
    
    // 限制分数在0-100之间
    socialScore = Math.min(100, Math.max(0, Math.round(socialScore)));
    
    // 更新全局状态
    PlatformState.esgScore.social = socialScore;
    updateESGVisualization();
    
    // 显示结果
    const resultHtml = `
        <div class="result-content">
            <h5><i class="fas fa-users text-primary me-2"></i>社会责任评估结果</h5>
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="result-item">
                        <span class="result-label">员工满意度：</span>
                        <span class="result-value">${employeeSatisfaction}%</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">年度培训：</span>
                        <span class="result-value">${trainingHours} 小时</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">员工流失率：</span>
                        <span class="result-value">${turnoverRate}%</span>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="result-item">
                        <span class="result-label">客户满意度：</span>
                        <span class="result-value">${customerSatisfaction}%</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">社区投入：</span>
                        <span class="result-value">${communityInvestment} 万元</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">供应商ESG评估：</span>
                        <span class="result-value">${supplierESG}分</span>
                    </div>
                </div>
            </div>
            <div class="alert ${socialScore >= 70 ? 'alert-success' : socialScore >= 50 ? 'alert-warning' : 'alert-danger'} mt-3">
                <i class="fas fa-handshake me-2"></i>
                <strong>社会(S)得分：${socialScore}分</strong> - 
                ${socialScore >= 80 ? '优秀的社会责任表现' : 
                  socialScore >= 60 ? '良好的社会责任基础' : 
                  '需要加强社会责任建设'}
            </div>
        </div>
    `;
    
    document.getElementById('calcResult').innerHTML = resultHtml;
    showToast('社会责任评估完成！', 'success');
}

/**
 * 计算治理绩效分数
 */
function calculateGovernance() {
    const ownershipType = document.getElementById('ownershipType').value;
    const governanceLevel = parseFloat(document.getElementById('governanceLevel').value) || 60;
    const independentDirectors = parseFloat(document.getElementById('independentDirectors').value) || 30;
    const femaleDirectors = parseFloat(document.getElementById('femaleDirectors').value) || 25;
    const complianceTraining = parseFloat(document.getElementById('complianceTraining').value) || 4;
    const antiCorruption = parseFloat(document.getElementById('antiCorruption').value) || 60;
    const esgDisclosure = parseFloat(document.getElementById('esgDisclosure').value) || 60;
    const auditIndependence = parseFloat(document.getElementById('auditIndependence').value) || 50;
    const riskManagement = parseFloat(document.getElementById('riskManagement').value) || 60;
    const dataSecurity = parseFloat(document.getElementById('dataSecurity').value) || 50;
    
    let governanceScore = 0;
    
    // 1. 董事会结构与独立性（25%权重）
    // - 独立董事比例（10%）
    let independentScore = 0;
    if (independentDirectors >= 40) independentScore = 100;
    else if (independentDirectors >= 30) independentScore = 80;
    else if (independentDirectors >= 20) independentScore = 60;
    else if (independentDirectors >= 10) independentScore = 40;
    else independentScore = 20;
    governanceScore += independentScore * 0.10;
    
    // - 女性董事比例（10%）
    let femaleScore = 0;
    if (femaleDirectors >= 40) femaleScore = 100;
    else if (femaleDirectors >= 30) femaleScore = 80;
    else if (femaleDirectors >= 20) femaleScore = 60;
    else if (femaleDirectors >= 10) femaleScore = 40;
    else femaleScore = 20;
    governanceScore += femaleScore * 0.10;
    
    // - 治理水平基础分（5%）
    governanceScore += governanceLevel * 0.05;
    
    // 2. 商业道德与合规（25%权重）
    // - 合规培训（10%）
    let trainingScore = 0;
    if (complianceTraining >= 6) trainingScore = 100;
    else if (complianceTraining >= 4) trainingScore = 80;
    else if (complianceTraining >= 2) trainingScore = 60;
    else trainingScore = 30;
    governanceScore += trainingScore * 0.10;
    
    // - 反腐败政策（15%）
    governanceScore += antiCorruption * 0.15;
    
    // 3. 透明度与披露（25%权重）
    // - ESG信息披露（15%）
    governanceScore += esgDisclosure * 0.15;
    
    // - 审计独立性（10%）
    governanceScore += auditIndependence * 0.10;
    
    // 4. 风险管理（25%权重）
    // - 风险管理制度（15%）
    governanceScore += riskManagement * 0.15;
    
    // - 数据安全（10%）
    governanceScore += dataSecurity * 0.10;
    
    // 5. 根据所有权性质调整
    if (ownershipType === 'state') {
        governanceScore *= 1.05; // 国有企业通常治理更规范
    } else if (ownershipType === 'foreign') {
        governanceScore *= 1.03; // 外资企业通常治理较好
    }
    
    // 限制分数在0-100之间
    governanceScore = Math.min(100, Math.max(0, Math.round(governanceScore)));
    
    // 更新全局状态
    PlatformState.esgScore.governance = governanceScore;
    updateESGVisualization();
    
    // 显示结果
    const resultHtml = `
        <div class="result-content">
            <h5><i class="fas fa-landmark text-info me-2"></i>公司治理分析结果</h5>
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="result-item">
                        <span class="result-label">独立董事比例：</span>
                        <span class="result-value">${independentDirectors}%</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">女性董事比例：</span>
                        <span class="result-value">${femaleDirectors}%</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">合规培训：</span>
                        <span class="result-value">${complianceTraining} 次/年</span>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="result-item">
                        <span class="result-label">ESG信息披露：</span>
                        <span class="result-value">${esgDisclosure}分</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">风险管理制度：</span>
                        <span class="result-value">${riskManagement}分</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">数据安全等级：</span>
                        <span class="result-value">${dataSecurity}分</span>
                    </div>
                </div>
            </div>
            <div class="alert ${governanceScore >= 70 ? 'alert-success' : governanceScore >= 50 ? 'alert-warning' : 'alert-danger'} mt-3">
                <i class="fas fa-balance-scale me-2"></i>
                <strong>治理(G)得分：${governanceScore}分</strong> - 
                ${governanceScore >= 80 ? '卓越的治理水平' : 
                  governanceScore >= 60 ? '规范的治理体系' : 
                  '需要完善治理结构'}
            </div>
        </div>
    `;
    
    document.getElementById('calcResult').innerHTML = resultHtml;
    showToast('公司治理分析完成！', 'success');
}

/**
 * 更新ESG可视化图表和分数显示
 */
function updateESGVisualization() {
    const envScore = PlatformState.esgScore.environment;
    const socialScore = PlatformState.esgScore.social;
    const governanceScore = PlatformState.esgScore.governance;
    
    // 计算总分（加权平均）
    const totalScore = Math.round(
        envScore * 0.4 + 
        socialScore * 0.3 + 
        governanceScore * 0.3
    );
    PlatformState.esgScore.total = totalScore;
    
    // 更新分数显示
    document.getElementById('envScore').textContent = envScore;
    document.getElementById('socialScore').textContent = socialScore;
    document.getElementById('govScore').textContent = governanceScore;
    
    // 更新进度条
    document.getElementById('envScoreBar').style.width = `${envScore}%`;
    document.getElementById('socialScoreBar').style.width = `${socialScore}%`;
    document.getElementById('govScoreBar').style.width = `${governanceScore}%`;
    
    // 更新雷达图数据
    updateRadarChartData([envScore, socialScore, governanceScore]);
    
    // 如果有总分显示，也更新
    const totalScoreElement = document.getElementById('totalScore');
    if (totalScoreElement) {
        totalScoreElement.textContent = totalScore;
    }
}

/**
 * 更新雷达图数据
 */
function updateRadarChartData(scores) {
    const chartDom = document.getElementById('esgRadarChart');
    if (!chartDom) return;
    
    const chart = echarts.getInstanceByDom(chartDom);
    if (!chart) return;
    
    // 更新当前表现的数据
    const option = chart.getOption();
    option.series[0].data[0].value = [
        scores[0], // 环境
        scores[1], // 社会
        scores[2], // 治理
        Math.round((scores[0] + scores[1]) / 2), // 综合1
        Math.round((scores[1] + scores[2]) / 2), // 综合2
        Math.round((scores[0] + scores[2]) / 2)  // 综合3
    ];
    
    chart.setOption(option);
}

/**
 * 初始化ESG计算器
 */
function initESGCalculator() {
    // 标签切换功能
    const calcTabs = document.querySelectorAll('.calc-tab');
    const calcPanels = document.querySelectorAll('.calc-panel');
    
    calcTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-target');
            
            // 更新标签状态
            calcTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // 显示对应面板
            calcPanels.forEach(panel => {
                panel.classList.remove('active');
                if (panel.id === target) {
                    panel.classList.add('active');
                }
            });
        });
    });
    
    // 输入框实时验证
    const numberInputs = document.querySelectorAll('.calculator-content input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('change', function() {
            const min = parseFloat(this.getAttribute('min')) || 0;
            const max = parseFloat(this.getAttribute('max')) || 100;
            let value = parseFloat(this.value) || 0;
            
            if (value < min) {
                this.value = min;
                showToast(`数值不能小于${min}`, 'warning');
            } else if (value > max) {
                this.value = max;
                showToast(`数值不能大于${max}`, 'warning');
            }
        });
    });
    
    // 初始化默认分数
    updateESGVisualization();
}

/**
 * 计算综合ESG分数并生成建议
 */
function calculateTotalESG() {
    const envScore = PlatformState.esgScore.environment;
    const socialScore = PlatformState.esgScore.social;
    const governanceScore = PlatformState.esgScore.governance;
    
    const totalScore = Math.round(
        envScore * 0.4 + 
        socialScore * 0.3 + 
        governanceScore * 0.3
    );
    
    // 生成改进建议
    let recommendations = [];
    
    if (envScore < 60) {
        recommendations.push('• 优化能源结构，提高能源使用效率');
        recommendations.push('• 加强废弃物管理和回收利用');
        recommendations.push('• 考虑使用清洁能源和可再生能源');
    }
    
    if (socialScore < 60) {
        recommendations.push('• 加强员工培训和职业发展支持');
        recommendations.push('• 改善员工福利和工作环境');
        recommendations.push('• 增加社区投入和社会责任项目');
    }
    
    if (governanceScore < 60) {
        recommendations.push('• 完善公司治理结构，增加独立董事比例');
        recommendations.push('• 加强合规培训和反腐败制度建设');
        recommendations.push('• 提高信息披露透明度');
    }
    
    // 显示综合结果
    const resultHtml = `
        <div class="result-content">
            <h5><i class="fas fa-chart-pie text-primary me-2"></i>ESG综合评估结果</h5>
            <div class="row mt-3">
                <div class="col-md-4 text-center">
                    <div class="score-circle ${envScore >= 70 ? 'score-high' : envScore >= 50 ? 'score-medium' : 'score-low'}">
                        <span class="score-circle-value">${envScore}</span>
                        <span class="score-circle-label">环境(E)</span>
                    </div>
                </div>
                <div class="col-md-4 text-center">
                    <div class="score-circle ${socialScore >= 70 ? 'score-high' : socialScore >= 50 ? 'score-medium' : 'score-low'}">
                        <span class="score-circle-value">${socialScore}</span>
                        <span class="score-circle-label">社会(S)</span>
                    </div>
                </div>
                <div class="col-md-4 text-center">
                    <div class="score-circle ${governanceScore >= 70 ? 'score-high' : governanceScore >= 50 ? 'score-medium' : 'score-low'}">
                        <span class="score-circle-value">${governanceScore}</span>
                        <span class="score-circle-label">治理(G)</span>
                    </div>
                </div>
            </div>
            
            <div class="total-score mt-4 text-center">
                <h4>综合ESG得分：<span class="text-gradient">${totalScore}/100</span></h4>
                <p class="text-muted">权重分配：环境40%，社会30%，治理30%</p>
            </div>
            
            ${recommendations.length > 0 ? `
            <div class="recommendations mt-4">
                <h6><i class="fas fa-lightbulb me-2"></i>改进建议：</h6>
                <ul class="list-unstyled">
                    ${recommendations.map(rec => `<li class="mb-2">${rec}</li>`).join('')}
                </ul>
            </div>
            ` : `
            <div class="alert alert-success mt-4">
                <i class="fas fa-trophy me-2"></i>
                恭喜！您的企业在ESG各方面表现良好，继续保持！
            </div>
            `}
            
            <div class="text-center mt-4">
                <button class="btn btn-primary me-2" onclick="generateReport('esg')">
                    <i class="fas fa-file-alt me-2"></i>生成ESG报告
                </button>
                <button class="btn btn-outline-primary" onclick="saveESGResults()">
                    <i class="fas fa-save me-2"></i>保存结果
                </button>
            </div>
        </div>
    `;
    
    document.getElementById('calcResult').innerHTML = resultHtml;
    
    // 显示评估等级
    let level = '';
    let color = '';
    if (totalScore >= 80) {
        level = '优秀';
        color = 'success';
    } else if (totalScore >= 60) {
        level = '良好';
        color = 'warning';
    } else {
        level = '待改进';
        color = 'danger';
    }
    
    showToast(`ESG综合评估完成！得分：${totalScore}（${level}）`, color);
}

/**
 * 保存ESG结果
 */
function saveESGResults() {
    const results = {
        timestamp: new Date().toISOString(),
        scores: PlatformState.esgScore,
        user: PlatformState.user,
        recommendations: []
    };
    
    // 添加到历史记录
    if (!PlatformState.carbonData.esgHistory) {
        PlatformState.carbonData.esgHistory = [];
    }
    PlatformState.carbonData.esgHistory.push(results);
    
    saveUserData();
    showToast('ESG评估结果已保存！', 'success');
}

// ============================================
// 工具初始化
// ============================================

/**
 * 初始化工具
 */
function initTools() {
    // 返回顶部按钮
    const scrollTopBtn = document.getElementById('scrollTopBtn');
    if (scrollTopBtn) {
        scrollTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // 主题切换按钮
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

/**
 * 初始化事件监听
 */
function initEventListeners() {
    // 响应式调整
    window.addEventListener('resize', debounce(() => {
        // 重新初始化图表
        const charts = echarts.getInstanceByDom(document.getElementById('heroDashboard'));
        if (charts) charts.resize();
    }, 250));
}

/**
 * 加载示例数据
 */
function loadSampleData() {
    // 可以在这里加载更多的模拟数据
    console.log('示例数据加载完成');
}

/**
 * 显示欢迎消息
 */
function showWelcomeMessage() {
    if (PlatformState.user) {
        showToast(`欢迎回来，${PlatformState.user.name}！`, 'success');
    } else {
        // 可以显示引导信息
        console.log('欢迎使用碳融智核平台！');
    }
}

// ============================================
// 其他功能函数
// ============================================

/**
 * 打开计算器
 */
function openCalculator(type) {
    if (type === 'esg') {
        // 滚动到ESG计算器
        const esgSection = document.getElementById('esg-calculator');
        if (esgSection) {
            window.scrollTo({
                top: esgSection.offsetTop - 80,
                behavior: 'smooth'
            });
        }
    } else if (type === 'carbon') {
        // 显示碳计算器模态框
        const modal = new bootstrap.Modal(document.getElementById('calculatorModal'));
        modal.show();
    }
}

/**
 * 申请金融产品
 */
function applyProduct(productId) {
    const product = DataService.financialProducts.find(p => p.id === productId);
    if (!product) return;
    
    if (PlatformState.user) {
        showModal('金融产品申请', `
            <div class="application-form">
                <h6><i class="fas fa-handshake me-2"></i>${product.name}</h6>
                <p class="text-muted">${product.description}</p>
                
                <div class="alert alert-info mt-3">
                    <i class="fas fa-info-circle me-2"></i>
                    申请要求：${product.requirements}
                </div>
                
                <form id="productApplicationForm">
                    <div class="mb-3">
                        <label class="form-label">申请金额（元）</label>
                        <input type="number" class="form-control" placeholder="请输入申请金额" min="10000" max="${product.maxAmount}" required>
                        <small class="text-muted">最高可申请：${product.maxAmount.toLocaleString()}元</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">使用用途</label>
                        <textarea class="form-control" rows="3" placeholder="请描述资金用途..." required></textarea>
                    </div>
                    <button type="submit" class="btn btn-success w-100">
                        <i class="fas fa-paper-plane me-2"></i>提交申请
                    </button>
                </form>
            </div>
        `);
    } else {
        showToast('请先登录后申请金融产品', 'warning');
        const modal = new bootstrap.Modal(document.getElementById('loginModal'));
        modal.show();
    }
}

/**
 * 查看解决方案详情
 */
function viewSolution(solutionType) {
    const solutions = {
        ecommerce: {
            title: '电商与零售解决方案',
            description: '针对订单履约、物流包装、退货处理等场景的全链条碳足迹管理',
            features: [
                '订单级碳核算与追踪',
                '智能包装优化建议',
                '绿色物流路径规划',
                '平台合规对接服务',
                '消费者碳足迹展示',
                '绿色商家认证支持'
            ],
            benefits: [
                '降低30%包装相关碳排放',
                '提升20%物流效率',
                '获得平台流量扶持',
                '增强消费者绿色信任'
            ]
        },
        manufacture: {
            title: '制造与加工解决方案',
            description: '覆盖生产能耗、原材料、供应链等环节的精细化碳管理',
            features: [
                '生产能耗实时监控',
                '供应链碳追溯系统',
                '绿色技改评估工具',
                '政策补贴申报辅助',
                '能源效率优化建议',
                '碳排放预测分析'
            ],
            benefits: [
                '降低25%生产能耗',
                '获得政府补贴支持',
                '提升ESG评级',
                '降低合规成本'
            ]
        },
        logistics: {
            title: '物流与运输解决方案',
            description: '优化运输路径、车辆能耗，降低物流环节碳排放强度',
            features: [
                '智能路径优化算法',
                '车辆能耗管理系统',
                '多式联运评估工具',
                '绿色车队认证支持',
                '碳排放实时监测',
                '驾驶员行为分析'
            ],
            benefits: [
                '减少15%燃油消耗',
                '优化运输路径效率',
                '获得绿色车队认证',
                '降低运营成本'
            ]
        }
    };
    
    const solution = solutions[solutionType] || solutions.ecommerce;
    
    showModal(solution.title, `
        <div class="solution-details">
            <p class="lead">${solution.description}</p>
            
            <div class="row mt-4">
                <div class="col-md-6">
                    <h6><i class="fas fa-star me-2"></i>核心功能</h6>
                    <ul class="list-unstyled">
                        ${solution.features.map(feature => `
                            <li class="mb-2"><i class="fas fa-check-circle text-success me-2"></i>${feature}</li>
                        `).join('')}
                    </ul>
                </div>
                <div class="col-md-6">
                    <h6><i class="fas fa-chart-line me-2"></i>预期效益</h6>
                    <ul class="list-unstyled">
                        ${solution.benefits.map(benefit => `
                            <li class="mb-2"><i class="fas fa-bullseye text-primary me-2"></i>${benefit}</li>
                        `).join('')}
                    </ul>
                </div>
            </div>
            
            <div class="alert alert-success mt-4">
                <i class="fas fa-lightbulb me-2"></i>
                <strong>适用企业：</strong>年营收1000万-5亿元，员工50-500人，希望提升ESG表现的中小企业
            </div>
            
            <div class="text-center mt-4">
                <button class="btn btn-primary me-2" onclick="showModal('咨询方案', '请填写您的联系信息，我们的顾问将为您提供定制化方案。')">
                    <i class="fas fa-phone me-2"></i>咨询方案
                </button>
                <button class="btn btn-outline-primary" onclick="openCalculator('esg')">
                    <i class="fas fa-calculator me-2"></i>免费评估
                </button>
            </div>
        </div>
    `, 'lg');
}

/**
 * 选择定价方案
 */
function selectPlan(planType) {
    const plans = {
        basic: {
            name: '基础版',
            price: '免费',
            action: '立即试用'
        },
        pro: {
            name: '专业版',
            price: '999元/年',
            action: '立即购买'
        },
        enterprise: {
            name: '企业版',
            price: '1999元/年',
            action: '咨询购买'
        }
    };
    
    const plan = plans[planType] || plans.basic;
    
    if (planType === 'basic') {
        if (PlatformState.user) {
            showToast('基础版已激活！您可以开始使用基础功能。', 'success');
        } else {
            showToast('请先注册账号以使用基础版功能', 'info');
            const modal = new bootstrap.Modal(document.getElementById('loginModal'));
            modal.show();
        }
    } else {
        showModal(`选择${plan.name}`, `
            <div class="plan-selection">
                <h5>${plan.name}</h5>
                <h3 class="text-primary my-4">${plan.price}</h3>
                
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    ${planType === 'pro' ? 
                        '专业版包含完整功能，适合中小企业日常使用' : 
                        '企业版提供定制化服务，适合有特殊需求的企业'}
                </div>
                
                <form id="planSelectionForm">
                    <div class="mb-3">
                        <label class="form-label">购买数量（用户数）</label>
                        <input type="number" class="form-control" value="1" min="1" max="100">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">购买时长</label>
                        <select class="form-select">
                            <option value="1">1年</option>
                            <option value="2">2年（享9折优惠）</option>
                            <option value="3">3年（享8折优惠）</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">联系人信息</label>
                        <input type="text" class="form-control" placeholder="姓名" required>
                    </div>
                    <div class="mb-3">
                        <input type="tel" class="form-control" placeholder="电话" required>
                    </div>
                    <div class="mb-3">
                        <input type="email" class="form-control" placeholder="邮箱" required>
                    </div>
                    
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="fas fa-shopping-cart me-2"></i>${plan.action}
                    </button>
                </form>
            </div>
        `);
    }
}

// ============================================
// 页面加载完成后的初始化
// ============================================

// 确保DOM完全加载后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initPlatform();
    });
} else {
    initPlatform();
}

// 导出到全局作用域
window.PlatformState = PlatformState;
window.DataService = DataService;
window.calculateEnvironmental = calculateEnvironmental;
window.calculateSocial = calculateSocial;
window.calculateGovernance = calculateGovernance;
window.calculateTotalESG = calculateTotalESG;
window.saveESGResults = saveESGResults;
window.openCalculator = openCalculator;
window.applyProduct = applyProduct;
window.viewSolution = viewSolution;
window.selectPlan = selectPlan;
window.useOCRData = useOCRData;
window.resetOCRDemo = resetOCRDemo;
window.loadSample = loadSample;
window.generateReport = generateReport;
window.downloadReport = downloadReport;
window.shareReport = shareReport;
window.saveToCloud = saveToCloud;
window.viewReportHistory = viewReportHistory;
window.toggleTheme = toggleTheme;
window.showToast = showToast;
window.showModal = showModal;


// --- GLOBAL UI HELPERS ---
function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = 'custom-toast';
    
    // Colors
    let iconColor = type === 'success' ? 'var(--success)' : 
                    type === 'warning' ? 'var(--warning)' : 
                    type === 'danger' ? 'var(--danger)' : 'var(--info)';
    let iconClass = type === 'success' ? 'fa-check-circle' : 
                    type === 'warning' ? 'fa-exclamation-triangle' : 
                    type === 'danger' ? 'fa-times-circle' : 'fa-info-circle';
                    
    toast.innerHTML = `<i class="fas ${iconClass}" style="color: ${iconColor}; font-size: 1.25rem;"></i><span>${message}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Ensure pages get fade-in class
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.tab-pane').forEach(page => {
        page.classList.add('page-content');
    });
    
    // Add simple num-roll effect to big numbers
    document.querySelectorAll('.fs-2, .fs-1, h2, h1').forEach(el => {
        if(!isNaN(parseFloat(el.innerText)) && el.innerText.length < 10) {
            el.classList.add('num-roll');
        }
    });
});
