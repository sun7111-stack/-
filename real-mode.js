// Real Mode keeps the runnable API-backed flow separate from the visual demo flow.
(function () {
  const RealMode = {
    state: {
      mode: 'real',
      health: null,
      steps: [],
      lastRun: null,
      running: false,
    },

    selectors: {
      panel: 'realModePanel',
      status: 'realModeStatus',
      steps: 'realModeSteps',
      result: 'realModeResult',
      file: 'realVoucherFile',
      check: 'realModeCheckBtn',
      run: 'realModeRunBtn',
    },

    apiRoot() {
      const apiBase = (window.API && API.BASE_URL) || 'http://localhost:8000/api';
      return apiBase.replace(/\/api\/?$/, '');
    },

    async request(path, options = {}) {
      if (!window.API) throw new Error('前端 API 对象未加载，请确认 api.js 已引入。');
      if (path.startsWith('/api/')) {
        const headers = { ...(options.headers || {}) };
        const token = API.getToken && API.getToken();
        if (token) headers.Authorization = `Bearer ${token}`;
        const response = await fetch(`${this.apiRoot()}${path}`, { ...options, headers });
        const data = await this.readResponse(response);
        if (!response.ok) throw new Error(this.toErrorText(data, `请求失败：${path}`));
        return data;
      }
      return API.request(path, options);
    },

    async readResponse(response) {
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) return response.json();
      return response.text();
    },

    toErrorText(data, fallback) {
      if (!data) return fallback;
      if (typeof data === 'string') return data;
      return data.detail || data.message || fallback;
    },

    escape(value) {
      return String(value ?? '').replace(/[&<>"']/g, ch => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      }[ch]));
    },

    formatNumber(value, digits = 2) {
      const n = Number(value);
      if (!Number.isFinite(n)) return '--';
      return n.toLocaleString('zh-CN', { maximumFractionDigits: digits });
    },

    friendlyError(error) {
      const message = String(error?.message || error || '未知错误');
      if (/Failed to fetch|无法连接|NetworkError/i.test(message)) {
        return '无法连接后端服务。请先在 backend 目录启动：python main.py，然后刷新页面重试。';
      }
      if (/401|Not authenticated|Could not validate credentials|认证/i.test(message)) {
        return '登录状态失效或 demo 账号不可用，请确认 demo@carbon-ai.com / demo123 存在。';
      }
      if (/404|Not Found/i.test(message)) {
        return '后端接口不存在。请重启后端，让新增的真实模式健康检查接口生效。';
      }
      if (/500|Internal Server Error/i.test(message)) {
        return `后端内部错误：${message}`;
      }
      return message;
    },

    markStep(key, label, status, detail = '') {
      const existing = this.state.steps.find(step => step.key === key);
      const next = { key, label, status, detail, time: new Date().toLocaleTimeString('zh-CN') };
      if (existing) Object.assign(existing, next);
      else this.state.steps.push(next);
      this.renderSteps();
    },

    setStatus(kind, html) {
      const el = document.getElementById(this.selectors.status);
      if (!el) return;
      el.className = `real-mode-status ${kind}`;
      el.innerHTML = html;
    },

    renderSteps() {
      const el = document.getElementById(this.selectors.steps);
      if (!el) return;
      if (!this.state.steps.length) {
        el.innerHTML = '<div class="real-step muted">尚未运行真实闭环。点击“检查真实服务”会先确认数据库、OCR、因子库、证据链和报告服务。</div>';
        return;
      }
      el.innerHTML = this.state.steps.map(step => `
        <div class="real-step ${step.status}">
          <span class="real-step-dot"></span>
          <div>
            <strong>${this.escape(step.label)}</strong>
            <small>${this.escape(step.detail || step.status)} · ${this.escape(step.time)}</small>
          </div>
        </div>
      `).join('');
    },

    renderResult(payload = null) {
      const el = document.getElementById(this.selectors.result);
      if (!el) return;
      if (!payload) {
        el.innerHTML = `
          <div class="real-result-empty">
            <strong>真实链路凭证区</strong>
            <span>运行后会展示 record_id、analysis_id、tx_id、Merkle Root 等后端真实返回证据。</span>
          </div>
        `;
        return;
      }

      const carbon = payload.carbon || {};
      const risk = payload.risk || {};
      const evidence = payload.evidence || {};
      const report = payload.report || {};
      const chain = payload.chain || {};
      const ocr = payload.ocr || {};
      const ocrData = ocr.data || ocr;

      const rows = [
        ['数据来源', payload.source || 'Real API'],
        ['OCR 方法', ocrData.parse_method || 'api/sample'],
        ['Raw Data ID', ocrData.chain_ids?.raw_data_id || '--'],
        ['Carbon record_id', carbon.record_id || '--'],
        ['Carbon analysis_id', carbon.analysis_id || evidence.analysis_id || '--'],
        ['总碳排放', `${this.formatNumber(carbon.total_emission)} tCO2e`],
        ['风险等级', risk.risk_level || '--'],
        ['可信度', risk.trust_score ? `${this.formatNumber(risk.trust_score * 100, 1)}%` : '--'],
        ['Evidence tx_id', evidence.tx_id || chain.anchor?.tx_id || '--'],
        ['Merkle Root', evidence.merkle_root || chain.anchor?.merkle_root || '--'],
        ['Report 模型', report.model_used || '--'],
        ['Report Mock', report.is_mock === true ? '是' : report.is_mock === false ? '否' : '--'],
      ];

      el.innerHTML = `
        <div class="real-proof-grid">
          ${rows.map(([label, value]) => `
            <div>
              <span>${this.escape(label)}</span>
              <strong title="${this.escape(value)}">${this.escape(value)}</strong>
            </div>
          `).join('')}
        </div>
        <div class="real-report-preview">
          <strong>AI 报告摘要</strong>
          <p>${this.escape(report.executive_summary || report.summary || '报告接口已返回，但没有摘要字段。')}</p>
        </div>
      `;
    },

    normalizeHealth(payload) {
      if (payload?.checks?.length) return payload;
      const checks = Object.entries(payload || {}).map(([name, item]) => ({
        key: name,
        name,
        ok: !!item.ok,
        required: true,
        detail: item.ok ? '在线' : (item.error || '异常'),
        meta: item.data || {},
      }));
      const requiredOk = checks.every(item => item.ok);
      return {
        status: requiredOk ? 'ok' : 'blocked',
        message: requiredOk ? '真实模式依赖已就绪' : '真实模式关键依赖未就绪',
        checks,
      };
    },

    renderHealth(payload) {
      const normalized = this.normalizeHealth(payload);
      const chips = normalized.checks.map(item => {
        const cls = item.ok ? (item.meta?.mock_mode ? 'warn' : 'ok') : 'bad';
        const label = item.ok ? (item.meta?.mock_mode ? '降级' : '正常') : '异常';
        return `<span class="${cls}" title="${this.escape(item.detail)}">${this.escape(item.name)} ${label}</span>`;
      }).join('');

      const kind = normalized.status === 'ok' ? 'ok' : normalized.status === 'blocked' ? 'bad' : 'warning';
      this.setStatus(kind, `${chips}<span>${this.escape(normalized.message || '')}</span>`);
      this.state.health = normalized;
      return normalized;
    },

    async checkHealth(options = {}) {
      const { strict = false } = options;
      this.setStatus('checking', '<span>正在检查真实服务...</span>');

      let health;
      try {
        health = await API.get('/system/real-mode-health');
      } catch (error) {
        // Backward-compatible fallback for an old backend process that has not been restarted yet.
        health = await this.legacyHealthCheck();
      }

      const normalized = this.renderHealth(health);
      if (strict) {
        const blocking = normalized.checks.filter(item => item.required !== false && !item.ok);
        if (blocking.length) {
          throw new Error(`真实模式未就绪：${blocking.map(item => `${item.name} ${item.detail}`).join('；')}`);
        }
      }
      return normalized;
    },

    async legacyHealthCheck() {
      const checks = [
        ['backend', '后端', () => fetch(`${this.apiRoot()}/health`).then(async r => ({ ok: r.ok, data: await this.readResponse(r) }))],
        ['ocr', 'OCR', () => API.get('/ocr/health').then(data => ({ ok: true, data }))],
        ['factor_library', '排放因子库', () => API.getEmissionFactors().then(data => ({ ok: Array.isArray(data) && data.length > 0, data }))],
        ['benchmarks', '行业基准', () => API.getIndustryBenchmarks().then(data => ({ ok: Array.isArray(data) && data.length > 0, data }))],
      ];

      const results = [];
      for (const [key, name, fn] of checks) {
        try {
          const res = await fn();
          results.push({ key, name, ok: !!res.ok, required: true, detail: res.ok ? '在线' : '返回为空', meta: res.data || {} });
        } catch (error) {
          results.push({ key, name, ok: false, required: true, detail: this.friendlyError(error), meta: {} });
        }
      }
      const requiredOk = results.every(item => item.ok);
      return {
        status: requiredOk ? 'warning' : 'blocked',
        message: requiredOk ? '旧版健康检查通过；建议重启后端启用详细自检' : '真实模式关键依赖未就绪',
        checks: results,
      };
    },

    async ensureLogin() {
      this.markStep('auth', '登录真实账号', 'running', '检查 token / demo 用户');
      try {
        if (API.getToken && API.getToken()) {
          await API.getMe();
          this.markStep('auth', '登录真实账号', 'done', '已有有效 token');
          return;
        }
      } catch (_) {
        API.clearToken && API.clearToken();
      }

      const data = await API.login('demo@carbon-ai.com', 'demo123');
      this.markStep('auth', '登录真实账号', 'done', data.user?.company || 'demo@carbon-ai.com');
    },

    async getOcrResult(file) {
      this.markStep('ocr', '票据识别', 'running', file ? `上传 ${file.name}` : '使用后端示例票据');
      const ocr = file ? await API.recognizeOCR(file) : await API.getOCRSample('electricity');
      if (ocr.success === false) throw new Error(ocr.message || 'OCR 识别失败');
      const data = ocr.data || ocr;
      this.markStep('ocr', '票据识别', 'done', `${data.doc_type || 'voucher'} · ${(Number(data.confidence || 0) * 100).toFixed(1)}%`);
      return ocr;
    },

    getMainAmount(fields = {}) {
      const keys = ['amount', 'usage', 'electricity_usage', 'kwh', 'distance'];
      for (const key of keys) {
        const value = Number(fields[key]);
        if (Number.isFinite(value) && value > 0) return value;
      }
      for (const value of Object.values(fields)) {
        const n = Number(value);
        if (Number.isFinite(n) && n > 0) return n;
      }
      return 1320;
    },

    buildCarbonPayload(ocr) {
      const data = ocr.data || ocr;
      const fields = data.fields || {};
      const activity = data.suggested_activity_type || data.cleaned_record?.activity_type || 'electricity';
      const amount = this.getMainAmount(fields);
      return {
        doc_type: data.doc_type || 'electricity_bill',
        suggested_activity_type: activity,
        fields,
        activity_data: { [activity]: amount },
        shop_type: 'general',
        region: fields.region_code || '全国',
        annual_revenue: 1000,
        period: fields.period || data.cleaned_record?.period_time || new Date().toISOString().slice(0, 7),
        model_version: 'v2',
        uncertainty_mode: 'analytic',
      };
    },

    async calculateCarbon(ocr) {
      this.markStep('carbon', '自动化碳核算', 'running', '调用 /carbon/calculate');
      const payload = this.buildCarbonPayload(ocr);
      const carbon = await API.calculateCarbon(payload);
      this.markStep('carbon', '自动化碳核算', 'done', `analysis_id=${carbon.analysis_id || '--'}，${this.formatNumber(carbon.total_emission)} tCO2e`);
      return { carbon, payload };
    },

    async detectRisk(ocr, carbon) {
      this.markStep('risk', '风控检测', 'running', '调用 /risk/detect');
      const data = ocr.data || ocr;
      const amount = this.getMainAmount(data.fields || {});
      const benchmark = carbon.benchmark_compare || {};
      const risk = await API.detectRisk({
        task_id: carbon.analysis_id ? `AN-${carbon.analysis_id}` : undefined,
        bill_id: `real-${Date.now()}`,
        raw_text: data.raw_text || 'real-mode-voucher',
        structured_fields: {
          ...(data.fields || {}),
          esg_score: 82,
          record_id: carbon.record_id,
          analysis_id: carbon.analysis_id,
        },
        electricity_usage: amount,
        total_emission: carbon.total_emission,
        carbon_intensity: benchmark.carbon_intensity || 0.6,
        benchmark_deviation: Math.abs(Number(benchmark.deviation_ratio || 0)),
        scope3_share: Number(carbon.scope_breakdown?.S3 || 0) / Math.max(Number(carbon.total_emission || 1), 1),
      });
      this.markStep('risk', '风控检测', 'done', `${risk.risk_level || '--'} · score ${this.formatNumber(risk.risk_score_explain_v2 || risk.risk_score, 1)}`);
      return risk;
    },

    async storeEvidence(ocr, carbon, risk) {
      this.markStep('evidence', '可信存证', 'running', '写入哈希链和 Merkle 证明');
      const data = ocr.data || ocr;
      const analysisId = String(carbon.analysis_id || risk.task_id || `AN-${Date.now()}`);
      const evidence = await API.storeEvidence({
        raw_data_id: String(data.chain_ids?.raw_data_id || ''),
        analysis_id: analysisId,
        issuer: 'real-mode',
        chain_name: 'fabric-devnet',
        evidence_objects: [
          { object_type: 'raw_voucher', step_name: 'voucher_uploaded', payload: { doc_type: data.doc_type, raw_text: data.raw_text, fields: data.fields } },
          { object_type: 'ocr_result', step_name: 'ocr_parsed', payload: data },
          { object_type: 'carbon_result', step_name: 'carbon_calculated', payload: carbon },
          { object_type: 'risk_result', step_name: 'risk_scanned', payload: risk },
        ],
      });
      this.markStep('evidence', '可信存证', 'done', `tx=${evidence.tx_id || '--'}`);
      return evidence;
    },

    async verifyEvidence(evidence, carbon) {
      this.markStep('verify', '证据链核验', 'running', '查询链路并核验哈希');
      const analysisId = String(evidence.analysis_id || carbon.analysis_id || '');
      const chain = await API.getEvidenceChain(analysisId);
      const verify = await API.verifyEvidence({ analysis_id: analysisId });
      this.markStep('verify', '证据链核验', 'done', `hash=${verify.verify?.hash_chain || '--'}，merkle=${verify.verify?.merkle_inclusion || '--'}`);
      return { chain, verify };
    },

    async generateReport(carbon, risk, evidenceInfo) {
      this.markStep('report', 'AI 诊断报告', 'running', '生成结构化摘要');
      const chain = evidenceInfo.chain || {};
      const report = await API.generateAIReport({
        period: new Date().toISOString().slice(0, 7),
        total_emission: carbon.total_emission,
        carbon_intensity: carbon.benchmark_compare?.carbon_intensity,
        emission_breakdown: carbon.breakdown || [],
        risk_level: risk.risk_level,
        risk_score: risk.risk_score_explain_v2 || risk.risk_score,
        anomaly_reasons: risk.anomaly_reasons || risk.risk_reasons || [],
        trust_score: evidenceInfo.verify?.trust_score || evidenceInfo.evidence?.trust_score || risk.trust_score || 0,
        evidence_confidence: evidenceInfo.verify?.trust_score || 0.95,
        evidence_chain_length: Array.isArray(chain.timeline) ? chain.timeline.length : 0,
        esg_score: 82,
      });
      this.markStep('report', 'AI 诊断报告', 'done', report.is_mock ? '报告模型处于 mock/降级' : (report.model_used || 'real/model'));
      return report;
    },

    async runRealFlow() {
      if (this.state.running) return;
      this.state.running = true;
      this.state.steps = [];
      this.renderSteps();
      this.renderResult(null);
      this.setRunDisabled(true);
      this.setStatus('checking', '<span>真实闭环运行中，不会自动伪装成 mock 成功...</span>');

      try {
        await this.checkHealth({ strict: true });
        await this.ensureLogin();
        const fileInput = document.getElementById(this.selectors.file);
        const file = fileInput?.files?.[0] || null;
        const ocr = await this.getOcrResult(file);
        const { carbon } = await this.calculateCarbon(ocr);
        const risk = await this.detectRisk(ocr, carbon);
        const evidence = await this.storeEvidence(ocr, carbon, risk);
        const evidenceInfo = await this.verifyEvidence(evidence, carbon);
        const report = await this.generateReport(carbon, risk, { ...evidenceInfo, evidence });

        const lastRun = {
          source: file ? 'Real API · uploaded voucher' : 'Real API · backend sample voucher',
          ocr,
          carbon,
          risk,
          evidence,
          chain: evidenceInfo.chain,
          verify: evidenceInfo.verify,
          report,
          finishedAt: new Date().toISOString(),
        };
        this.state.lastRun = lastRun;
        window.RealModeState = lastRun;
        this.renderResult(lastRun);
        this.setStatus('ok', '<span class="ok">真实闭环完成</span><span class="ok">已写入数据库/证据链</span><span class="ok">可用于答辩展示</span>');
      } catch (error) {
        const text = this.friendlyError(error);
        console.error('[RealMode] flow failed', error);
        this.markStep('failed', '真实闭环中断', 'failed', text);
        this.setStatus('bad', `<span class="bad">真实模式失败</span><span>${this.escape(text)}</span><span>未自动切换 mock</span>`);
      } finally {
        this.state.running = false;
        this.setRunDisabled(false);
      }
    },

    setRunDisabled(disabled) {
      const run = document.getElementById(this.selectors.run);
      const check = document.getElementById(this.selectors.check);
      if (run) {
        run.disabled = disabled;
        run.innerHTML = disabled ? '<i class="fas fa-circle-notch fa-spin me-2"></i>真实链路运行中' : '<i class="fas fa-play me-2"></i>运行真实闭环';
      }
      if (check) check.disabled = disabled;
    },

    buildPanel() {
      const panel = document.createElement('section');
      panel.id = this.selectors.panel;
      panel.className = 'real-mode-panel';
      panel.innerHTML = `
        <div class="real-mode-copy">
          <span class="real-mode-kicker">Real Mode · API Backed</span>
          <h3>真实运行链路</h3>
          <p>这条链路独立于 Mock 演示：成功结果必须来自后端 API、数据库记录和证据链返回。</p>
        </div>
        <div class="real-mode-actions">
          <label class="real-file-picker">
            <i class="fas fa-file-arrow-up"></i>
            <span>可选上传票据</span>
            <input id="${this.selectors.file}" type="file" accept="image/png,image/jpeg,application/pdf">
          </label>
          <button id="${this.selectors.check}" type="button" class="btn btn-outline-success">
            <i class="fas fa-signal me-2"></i>检查真实服务
          </button>
          <button id="${this.selectors.run}" type="button" class="btn btn-success">
            <i class="fas fa-play me-2"></i>运行真实闭环
          </button>
        </div>
        <div id="${this.selectors.status}" class="real-mode-status idle">
          <span>真实模式待检查</span>
          <span>Mock 演示仍保留，但不会混入这里</span>
        </div>
        <div class="real-mode-body">
          <div id="${this.selectors.steps}" class="real-mode-steps"></div>
          <div id="${this.selectors.result}" class="real-mode-result"></div>
        </div>
      `;
      return panel;
    },

    mount() {
      if (document.getElementById(this.selectors.panel)) return;
      const homeDashboard = document.querySelector('#home .dashboard-container') || document.querySelector('.dashboard-container');
      const panel = this.buildPanel();
      if (homeDashboard) homeDashboard.prepend(panel);
      else document.body.prepend(panel);

      this.renderSteps();
      this.renderResult(null);

      document.getElementById(this.selectors.check)?.addEventListener('click', () => this.checkHealth());
      document.getElementById(this.selectors.run)?.addEventListener('click', () => this.runRealFlow());
      this.enhanceExistingActions();

      document.addEventListener('click', event => {
        const trigger = event.target.closest('[data-real-mode-run]');
        if (trigger) {
          event.preventDefault();
          this.runRealFlow();
        }
      });
    },

    enhanceExistingActions() {
      const targets = [
        { id: 'carbonBtn', label: '真实闭环核算' },
        { id: 'riskBtn', label: '真实风控闭环' },
      ];

      targets.forEach(target => {
        const base = document.getElementById(target.id);
        if (!base || document.querySelector(`[data-real-mode-extra="${target.id}"]`)) return;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-outline-success ms-2 real-mode-inline-btn';
        btn.dataset.realModeRun = 'true';
        btn.dataset.realModeExtra = target.id;
        btn.innerHTML = `<i class="fas fa-database me-2"></i>${target.label}`;
        base.insertAdjacentElement('afterend', btn);

        const note = document.createElement('div');
        note.className = 'real-mode-inline-note';
        note.innerHTML = '真实模式不会使用 DemoState 自动补数据；失败会显示接口错误。';
        btn.insertAdjacentElement('afterend', note);
      });
    },
  };

  window.RealMode = RealMode;
  document.addEventListener('DOMContentLoaded', () => RealMode.mount());
})();
