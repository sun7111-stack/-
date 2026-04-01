/**
 * js/app.js
 * 核心职责：系统启动入口，负责初始化全局配置、状态及按序启动各模块 
 */

// 1. 全局配置 [从原 script.js 迁移]
const CONFIG = {
    API_BASE_URL: 'https://api.carbon-ai.com/v1',
    LOCAL_STORAGE_KEY: 'carbon_platform_data',
    THEME_KEY: 'carbon_platform_theme',
    USER_KEY: 'carbon_platform_user',
    VERSION: '2.0.0'
};

// 2. 全局状态管理 [从原 script.js 迁移]
const PlatformState = {
    user: null,
    theme: 'light',
    currentPage: 'home',
    esgScore: { environment: 65, social: 70, governance: 75, total: 70 },
    carbonData: {},
    reportHistory: [],
    isInitialized: false
};

// 3. 通用工具函数 (供全局调用) [从原 script.js 迁移]
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

function showToast(message, type = 'info') {
    const existingToast = document.querySelector('.custom-toast');
    if (existingToast) existingToast.remove();
    const toast = document.createElement('div');
    toast.className = `custom-toast alert alert-${type} alert-dismissible fade show`;
    toast.style.cssText = `position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;`;
    const iconMap = { success: 'check-circle', error: 'exclamation-circle', warning: 'exclamation-triangle', info: 'info-circle' };
    toast.innerHTML = `<div class="d-flex align-items-center"><i class="fas fa-${iconMap[type] || 'info-circle'} me-2"></i><div class="flex-grow-1">${message}</div><button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>`;
    document.body.appendChild(toast);
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, 5000);
}

function showModal(title, content, size = 'md') {
    const existingModal = document.getElementById('dynamicModal');
    if (existingModal) existingModal.remove();
    const modal = document.createElement('div');
    modal.id = 'dynamicModal';
    modal.className = 'modal fade';
    modal.tabIndex = '-1';
    const modalDialogClass = size === 'lg' ? 'modal-lg' : size === 'xl' ? 'modal-xl' : '';
    modal.innerHTML = `<div class="modal-dialog ${modalDialogClass}"><div class="modal-content"><div class="modal-header"><h5 class="modal-title">${title}</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body">${content}</div><div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button></div></div></div>`;
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    modal.addEventListener('hidden.bs.modal', () => modal.remove());
}

// 4. UI 基础初始化逻辑
function initTheme() {
    const savedTheme = localStorage.getItem(CONFIG.THEME_KEY) || 'light';
    PlatformState.theme = savedTheme;
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function initForms() {
   if (typeof initLoginForm === 'function') initLoginForm();
    if (typeof initRegisterForm === 'function') initRegisterForm();
    if (typeof initContactForm === 'function') initContactForm();
}
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
// 修改 js/app.js 最后的启动入口
document.addEventListener('DOMContentLoaded', async function () {
    console.log('🚀 系统启动中...');
    
    // 1. 基础 UI 初始化
    initTheme();
    initTools();
    initEventListeners();
    initForms();

    // 2. 核心业务流程初始化
    await restoreSession(); 
    initSidebar();
    initPageRouter();
    initDemoFlow();

    // 3. 收尾工作
    loadSampleData();
    showWelcomeMessage();
    PlatformState.isInitialized = true;

    // ★ 关键新增：初始化完成后隐藏加载遮罩层
    const loader = document.getElementById('loadingOverlay');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => {
            loader.style.display = 'none';
        }, 500); // 配合 CSS 中的 0.5s 过渡动画
    }
});