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
    // 统一退出登录逻辑 [cite: 126-131]
if (logoutBtn) {
    logoutBtn.addEventListener('click', function(e) { 
        e.preventDefault();
        API.logout(); // 调用 api.js 中的清除 Token 逻辑 [cite: 128]
        PlatformState.user = null; // 重置全局状态 [cite: 130]
        showLoginPage(); // 返回登录界面 [cite: 131]
        showToast('已成功退出登录', 'success');
    });
}
}
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
// 新增 auth.js 核心函数 restoreSession() (来自任务文档 2.3)
/**
 * 2.1 优化目标：只信任 token，不依赖本地布尔值 [cite: 71, 72]
 */
async function restoreSession() {
    const token = API.getToken();
    const loginPage = document.getElementById('loginPage');
    const appMain = document.getElementById('appMain');

    // 1. 如果连 Token 都没有，直接展示登录页 [cite: 84, 85]
    if (!token) {
        showLoginPage();
        return;
    }

    try {
        // 2. 页面刷新调用 /api/auth/me 校验 token 有效性 
        const me = await API.getMe();
        
        // 3. 校验成功：存入全局状态，并进入主系统 [cite: 115, 116, 117]
        PlatformState.user = me;
        loginPage.style.display = 'none';
        appMain.style.display = 'flex';
        
        // 4. 回填用户信息界面 [cite: 118]
        loadUserInfo(); 
        
    } catch (error) {
        // 5. 校验失败（Token 过期或伪造）：自动清除并跳转登录 [cite: 75, 120, 121]
        console.error('登录校验失败:', error);
        API.clearToken();
        showLoginPage();
    }
}

// 辅助函数：统一显示登录页的逻辑
function showLoginPage() {
    const loginPage = document.getElementById('loginPage');
    const appMain = document.getElementById('appMain');
    if (loginPage) loginPage.style.display = 'flex';
    if (appMain) appMain.style.display = 'none';
}