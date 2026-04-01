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
//初始化页面路由
function initPageRouter() {
    // 监听所有带有 data-page 的点击（包括侧边栏和内页按钮）
    document.addEventListener('click', (e) => {
        const trigger = e.target.closest('[data-page]');
        if (trigger) {
            const pageId = trigger.getAttribute('data-page');
            switchPage(pageId);
        }
    });

    // 处理浏览器前进/后退
    window.addEventListener('hashchange', () => {
        const pageId = window.location.hash.replace('#', '') || 'home';
        switchPage(pageId);
    });
}
// 页面切换函数
function switchPage(pageId) {
    const sections = document.querySelectorAll('.page-section');
    const menuItems = document.querySelectorAll('.menu-item');
    const targetSection = document.getElementById(pageId);

    if (!targetSection) return;

    // 1. 隐藏所有页面并移除内联 display 样式
    sections.forEach(s => {
        s.classList.remove('active');
        s.style.display = 'none'; // 强制隐藏并覆盖 HTML 里的 inline style
    });

    // 2. 显示目标页面
    targetSection.classList.add('active');
    targetSection.style.display = 'block'; // 强制显示

    // 3. 更新侧边栏高亮
    menuItems.forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-page') === pageId) {
            item.classList.add('active');
        }
    });

    // 4. 同步 URL 哈希
    window.history.pushState(null, null, `#${pageId}`);

    // 5. 触发 resize 确保 ECharts 图表渲染正常
    setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
    }, 100);
}
function initContactForm() {
    const contactForm = document.getElementById('contactForm');
    if (!contactForm) return;
    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();
        showToast('咨询已提交！', 'success');
    });
}