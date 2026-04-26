// ============================================
// 碳融智核平台 - API服务层
// 负责与后端FastAPI通信
// ============================================

const API = {
    BASE_URL: 'http://localhost:8000/api',

    // 获取存储的JWT token
    getToken() {
        return localStorage.getItem('carbon_platform_token');
    },

    // 存储JWT token
    setToken(token) {
        localStorage.setItem('carbon_platform_token', token);
    },

    // 清除token
    clearToken() {
        localStorage.removeItem('carbon_platform_token');
    },

    // 通用请求方法
    async request(endpoint, options = {}) {
        const url = `${this.BASE_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            // 处理非JSON响应
            const contentType = response.headers.get('content-type');
            let data;
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }

            if (!response.ok) {
                const errorMsg = typeof data === 'object' ? (data.detail || '请求失败') : data;
                throw new Error(errorMsg);
            }

            return data;
        } catch (error) {
            if (error.message === 'Failed to fetch') {
                throw new Error('无法连接到服务器，请确保后端服务已启动');
            }
            throw error;
        }
    },

    // GET 请求
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    // POST 请求
    async post(endpoint, body) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body),
        });
    },

    // PUT 请求
    async put(endpoint, body) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body),
        });
    },

    // DELETE 请求
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },

    // 文件上传
    async upload(endpoint, file) {
        const url = `${this.BASE_URL}${endpoint}`;
        const formData = new FormData();
        formData.append('file', file);

        const headers = {};
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers,
                body: formData,
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || '上传失败');
            }
            return data;
        } catch (error) {
            if (error.message === 'Failed to fetch') {
                throw new Error('无法连接到服务器');
            }
            throw error;
        }
    },

    // ========== 认证相关 ==========

    async login(email, password) {
        const data = await this.post('/auth/login', { email, password });
        this.setToken(data.access_token);
        return data;
    },

    async register(userData) {
        const data = await this.post('/auth/register', userData);
        this.setToken(data.access_token);
        return data;
    },

    // 获取图形验证码
    async getCaptcha() {
        return this.get('/auth/captcha');
    },

    // 发送短信验证码（需先通过图形验证码）
    async sendSmsCode(phone, captchaId, captcha) {
        return this.post('/auth/sms-code', { phone, captcha_id: captchaId, captcha });
    },

    // 手机号+验证码登录（自动注册）
    async loginByPhone(phone, smsCode) {
        const data = await this.post('/auth/login/phone', { phone, sms_code: smsCode });
        this.setToken(data.access_token);
        return data;
    },

    // 企业账号+密码登录
    async loginByEnterprise(account, password) {
        const data = await this.post('/auth/login/enterprise', { account, password });
        this.setToken(data.access_token);
        return data;
    },

    // 访客预览
    async getVisitorPreview() {
        return this.get('/auth/visitor-preview');
    },

    async getMe() {
        return this.get('/auth/me');
    },

    async updateProfile(profileData) {
        return this.put('/auth/me', profileData);
    },

    logout() {
        this.clearToken();
    },

    // ========== 碳排放相关 ==========

    async getEmissionFactors() {
        return this.get('/carbon/emission-factors');
    },

    async getIndustryBenchmarks() {
        return this.get('/carbon/industry-benchmarks');
    },

    async calculateCarbon(calcData) {
        return this.post('/carbon/calculate', calcData);
    },

  async getCarbonRecords(params = '') {
    return this.get(`/carbon/records${params ? `?${params}` : ''}`);
},

    // ========== ESG评分相关 ==========

    async calculateESGEnvironment(data) {
        return this.post('/esg/calculate/environment', data);
    },

    async calculateESGSocial(data) {
        return this.post('/esg/calculate/social', data);
    },

    async calculateESGGovernance(data) {
        return this.post('/esg/calculate/governance', data);
    },

    async calculateESGTotal(data) {
        return this.post('/esg/calculate/total', data);
    },

    async getESGHistory() {
        return this.get('/esg/history');
    },

    // ========== 金融产品相关 ==========

    async getFinancialProducts() {
        return this.get('/finance/products');
    },

    async getFinancialProduct(id) {
        return this.get(`/finance/products/${id}`);
    },

    async applyFinancialProduct(applicationData) {
        return this.post('/finance/apply', applicationData);
    },

    async getApplications() {
        return this.get('/finance/applications');
    },

    // ========== 报告相关 ==========

    async getReportTemplates() {
        return this.get('/reports/templates');
    },

    async generateReport(reportData) {
        return this.post('/reports/generate', reportData);
    },

    async getReports() {
        return this.get('/reports');
    },

    async getPolicies() {
        return this.get('/policies');
    },

    async getCaseStudies() {
        return this.get('/cases');
    },

    async submitContact(contactData) {
        return this.post('/contact', contactData);
    },
// ========== 任务 6：演示主流程核心接口 ==========
    
    // 碳核算接口 [对接真实计算引擎]
    async calculateCarbon(data) {
        return this.post('/carbon/calculate', data);
    },

    // 风险检测接口 [对接区块链存证逻辑]
    async detectRisk(data) {
        return this.post('/risk/detect', data);
    },

    // 证据链写入
    async storeEvidence(data) {
        return this.post('/evidence/store', data);
    },

    // 查询证据链
    async getEvidenceChain(recordId) {
        return this.get(`/evidence/chain/${recordId}`);
    },

    // 证据链验真
    async verifyEvidence(data) {
        return this.post('/evidence/verify', data);
    },

    // 获取单叶子默克尔证明
    async getEvidenceProof(leafId) {
        return this.get(`/evidence/proof/${leafId}`);
    },

    // AI 诊断报告接口 [对接大模型分析逻辑]
    async generateAIReport(data) {
        return this.post('/reports/generate-ai', data);
    },
    // ========== OCR相关 ==========

    async recognizeOCR(file) {
        return this.upload('/ocr/recognize', file);
    },

    // 月度碳排时序预测 + Conformal 区间
    async forecastMonthlyCarbon(data) {
        return this.post('/forecast/monthly-carbon', data);
    },
// ========== 首页 / 驾驶舱相关 ==========

// 首页统计数据
async getDashboardStats() {
    return this.get('/dashboard/key-indicators');
},

// 首页最新事件流
async getLatestEvents(limit = 8) {
    return this.get(`/events/latest?limit=${limit}`);
},

// ========== 报告 / 数据列表补充接口 ==========

// 获取碳核算记录（支持后续扩展查询参数）
async getCarbonRecords(params = '') {
    return this.get(`/carbon/records${params ? `?${params}` : ''}`);
},

// 获取我的报告列表
async getMyReports() {
    return this.get('/reports/my-reports');
},

// 月度碳排预测（别名，后面统一调用）
async getMonthlyCarbonForecast(data) {
    return this.post('/forecast/monthly-carbon', data);
},
// 获取金融产品推荐
async getFinanceRecommendations(params = '') {
    return this.get(`/finance/recommendations${params ? `?${params}` : ''}`);
},
// ========== 系统健康检查 ==========

// 真实运行模式健康检查
async getRealModeHealth() {
    return this.get('/system/real-mode-health');
},
    async getOCRSample(type) {
        return this.get(`/ocr/sample/${type}`);
    },
};

// 导出到全局
window.API = API;
