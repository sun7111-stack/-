// Dynamic presentation layer requested by the review notes:
// force graph, live feed, business-flow sidebar, carbon topology, and readable evidence chain.
(function () {
  const HomeDynamics = {
    graphChart: null,
    topologyChart: null,
    feedTimer: null,
    nodeIndexByRole: {},

    init() {
      // Keep the original sidebar order requested by the user.
      // The business-flow sidebar builder is retained below as an optional helper,
      // but it is intentionally not invoked.
      this.mountHomeForceGraph();
      this.mountLiveFeed();
      this.bindKpiHover();
      this.mountCarbonTopology();
      this.mountEvidenceNarrative();
      window.addEventListener('resize', () => {
        this.graphChart && this.graphChart.resize();
        this.topologyChart && this.topologyChart.resize();
      });
    },

    rebuildSidebar() {
      const menu = document.querySelector('.sidebar-menu');
      if (!menu || menu.dataset.businessFlowReady === 'true') return;
      menu.dataset.businessFlowReady = 'true';

      const groups = [
        {
          title: '数据采集端',
          icon: 'fa-database',
          items: [
            ['demo-upload', '凭证上传与识别', 'fa-file-invoice'],
            ['features', '历史数据同步 / IoT接入', 'fa-satellite-dish'],
          ],
        },
        {
          title: '智能核算引擎',
          icon: 'fa-microchip',
          items: [
            ['demo-carbon', '自动化碳核算', 'fa-calculator'],
            ['esg-calculator', 'ESG智能计算器', 'fa-chart-pie'],
          ],
        },
        {
          title: '风控与报告中心',
          icon: 'fa-shield-halved',
          items: [
            ['demo-risk', '绿色金融风控扫描', 'fa-shield-alt'],
            ['demo-report', '智能诊断与报告生成', 'fa-file-signature'],
            ['data-center', '数据报告中心', 'fa-folder-open'],
          ],
        },
        {
          title: '金融产品超市',
          icon: 'fa-building-columns',
          items: [
            ['finance-match', '绿色信贷智能匹配', 'fa-handshake'],
            ['solutions', '行业解决方案', 'fa-gem'],
            ['cases', '客户成功案例', 'fa-briefcase'],
          ],
        },
        {
          title: '系统管理',
          icon: 'fa-gear',
          items: [
            ['about', '关于我们', 'fa-info-circle'],
            ['settings', '系统设置', 'fa-cog'],
          ],
        },
      ];

      menu.innerHTML = `
        <ul class="menu-list business-flow-menu">
          <li class="menu-item active" data-page="home">
            <a href="#home" class="menu-link"><i class="fas fa-home"></i><span>首页驾驶舱</span></a>
          </li>
          ${groups.map((group, idx) => `
            <li class="business-menu-group ${idx === 0 ? 'open' : ''}">
              <button class="menu-title business-menu-title" type="button">
                <span><i class="fas ${group.icon}"></i>${group.title}</span>
                <i class="fas fa-chevron-down"></i>
              </button>
              <ul class="sub" style="display:${idx < 4 ? 'block' : 'none'};">
                ${group.items.map(([page, label, icon]) => `
                  <li class="menu-item" data-page="${page}">
                    <a href="#${page}" class="menu-link"><i class="fas ${icon}"></i><span>${label}</span></a>
                  </li>
                `).join('')}
              </ul>
            </li>
          `).join('')}
        </ul>
      `;

      menu.querySelectorAll('.business-menu-title').forEach(title => {
        title.addEventListener('click', () => {
          const group = title.closest('.business-menu-group');
          const sub = group.querySelector('.sub');
          const open = sub.style.display !== 'none';
          sub.style.display = open ? 'none' : 'block';
          group.classList.toggle('open', !open);
        });
      });

      menu.querySelectorAll('.menu-item[data-page] .menu-link').forEach(link => {
        link.addEventListener('click', event => {
          const page = link.closest('.menu-item')?.dataset.page;
          if (!page) return;
          if (typeof switchPage === 'function') {
            event.preventDefault();
            switchPage(page);
            window.location.hash = page;
          }
          menu.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active'));
          link.closest('.menu-item')?.classList.add('active');
        });
      });
    },

    mountHomeForceGraph() {
      const panel = document.querySelector('.hero-insight-panel');
      if (!panel || panel.dataset.forceReady === 'true') return;
      panel.dataset.forceReady = 'true';
      panel.innerHTML = `
        <div class="insight-header">
          <div>
            <span class="insight-kicker">Carbon Chain Network</span>
            <h3>链上碳数据流转图</h3>
          </div>
          <span class="insight-status">Live</span>
        </div>
        <div id="homeForceGraph" class="home-force-graph"></div>
        <div class="force-flow-rail" aria-hidden="true">
          <span>Data</span><i></i><span>Engine</span><i></i><span>Chain</span><i></i><span>Finance</span>
        </div>
        <div class="force-graph-caption">
          <span><i class="dot dot-voucher"></i>数据凭证</span>
          <span><i class="dot dot-chain"></i>链上存证</span>
          <span><i class="dot dot-finance"></i>绿色金融</span>
        </div>
      `;

      if (typeof echarts === 'undefined') return;
      const chart = echarts.init(document.getElementById('homeForceGraph'));
      const nodes = [
        { name: '企业', role: 'enterprise', value: 42, category: 0, symbolSize: 34 },
        { name: '电费账单', role: 'voucher', value: 30, category: 1, symbolSize: 26 },
        { name: '物流单据', role: 'voucher', value: 28, category: 1, symbolSize: 25 },
        { name: 'OCR识别', role: 'engine', value: 34, category: 2, symbolSize: 27 },
        { name: '碳核算', role: 'carbon', value: 40, category: 2, symbolSize: 30 },
        { name: '风控模型', role: 'risk', value: 35, category: 3, symbolSize: 27 },
        { name: '区块链存证', role: 'chain', value: 38, category: 4, symbolSize: 29 },
        { name: '绿色银行', role: 'finance', value: 32, category: 5, symbolSize: 27 },
        { name: '信贷产品', role: 'finance', value: 26, category: 5, symbolSize: 24 },
      ];
      this.nodeIndexByRole = nodes.reduce((acc, node, index) => {
        acc[node.role] = acc[node.role] || [];
        acc[node.role].push(index);
        return acc;
      }, {});

      chart.setOption({
        tooltip: {
          borderWidth: 0,
          backgroundColor: 'rgba(23,32,51,0.92)',
          textStyle: { color: '#fff' },
          formatter: params => `${params.data.name}<br/>业务节点：${params.data.role}`,
        },
        legend: { show: false },
        animationDuration: 900,
        animationEasingUpdate: 'cubicOut',
        series: [{
          type: 'graph',
          layout: 'force',
          roam: false,
          draggable: true,
          left: 22,
          right: 22,
          top: 16,
          bottom: 18,
          force: {
            repulsion: 95,
            edgeLength: [46, 78],
            gravity: 0.22,
            friction: 0.58,
            layoutAnimation: true,
          },
          categories: [
            { name: 'Enterprise' },
            { name: 'Voucher' },
            { name: 'Engine' },
            { name: 'Risk' },
            { name: 'Chain' },
            { name: 'Finance' },
          ],
          data: nodes,
          links: [
            ['企业', '电费账单'], ['企业', '物流单据'], ['电费账单', 'OCR识别'],
            ['物流单据', 'OCR识别'], ['OCR识别', '碳核算'], ['碳核算', '风控模型'],
            ['风控模型', '区块链存证'], ['区块链存证', '绿色银行'], ['绿色银行', '信贷产品'],
          ].map(([source, target]) => ({ source, target })),
          edgeSymbol: ['none', 'arrow'],
          edgeSymbolSize: [0, 6],
          label: {
            show: true,
            color: '#172033',
            fontWeight: 800,
            fontSize: 10,
            formatter: '{b}',
            position: 'bottom',
            distance: 4,
          },
          itemStyle: {
            borderWidth: 2,
            borderColor: '#fff',
            shadowBlur: 14,
            shadowColor: 'rgba(31,107,79,0.16)',
          },
          lineStyle: { color: '#9bb7ad', opacity: 0.42, width: 1.7, curveness: 0.18 },
          emphasis: {
            focus: 'adjacency',
            itemStyle: { shadowBlur: 28, shadowColor: 'rgba(31,107,79,0.45)' },
            lineStyle: { opacity: 0.75, width: 4 },
          },
        }],
        color: ['#172033', '#1f6b4f', '#5e748c', '#b7791f', '#0f766e', '#2563eb'],
      });
      this.graphChart = chart;
      this.startGraphPulse();
    },

    startGraphPulse() {
      const roles = ['voucher', 'engine', 'carbon', 'risk', 'chain', 'finance'];
      let idx = 0;
      setInterval(() => {
        if (!this.graphChart) return;
        this.graphChart.dispatchAction({ type: 'downplay', seriesIndex: 0 });
        this.highlightRole(roles[idx % roles.length], 1200);
        idx += 1;
      }, 2400);
    },

    highlightRole(role, duration = 1600) {
      if (!this.graphChart) return;
      this.graphChart.dispatchAction({ type: 'downplay', seriesIndex: 0 });
      (this.nodeIndexByRole[role] || []).forEach(dataIndex => {
        this.graphChart.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex });
      });
      window.clearTimeout(this.highlightTimer);
      this.highlightTimer = window.setTimeout(() => {
        this.graphChart && this.graphChart.dispatchAction({ type: 'downplay', seriesIndex: 0 });
      }, duration);
    },

    bindKpiHover() {
      const cards = document.querySelectorAll('#home .stat-cards-row .stat-card');
      const roles = ['voucher', 'carbon', 'risk', 'finance'];
      cards.forEach((card, index) => {
        card.dataset.graphRole = roles[index] || 'enterprise';
        card.addEventListener('mouseenter', () => {
          card.classList.add('kpi-linked');
          this.highlightRole(card.dataset.graphRole, 2200);
        });
        card.addEventListener('mouseleave', () => card.classList.remove('kpi-linked'));
      });
    },

    mountLiveFeed() {
      const anchor = document.querySelector('.home-panorama-card') || document.querySelector('#home .stat-cards-row');
      if (!anchor || document.getElementById('homeLiveFeed')) return;
      const feed = document.createElement('section');
      feed.id = 'homeLiveFeed';
      feed.className = 'home-live-feed';
      feed.innerHTML = `
        <div class="live-feed-header">
          <div>
            <span class="insight-kicker">Realtime Operations</span>
            <h3>系统动态信息流</h3>
          </div>
          <span class="live-dot">运行中</span>
        </div>
        <div id="homeLiveFeedList" class="home-live-feed-list"></div>
      `;
      anchor.insertAdjacentElement('afterend', feed);

      const seeds = [
        ['OCR识别', '绿能科技', '成功提取电费账单字段，用电量 1320 kWh', 'ocr'],
        ['数据上链', '环宇制造', '碳排放凭证已存证，哈希: 0x66bd4625', 'chain'],
        ['风控预警', '城配物流', '发现运输轨迹与油耗不符，拦截洗绿风险', 'risk'],
        ['碳核算', '未来出行', 'Scope 2 排放完成核算，较上月下降 5.6%', 'carbon'],
        ['金融匹配', '绿创电子', '匹配到绿色信贷产品，预计利率优惠 45BP', 'finance'],
      ];
      seeds.slice(0, 4).forEach(item => this.pushFeed(item));
      let index = 4;
      this.feedTimer = setInterval(() => {
        this.pushFeed(seeds[index % seeds.length]);
        index += 1;
      }, 4200);
    },

    pushFeed([tag, company, message, type]) {
      const list = document.getElementById('homeLiveFeedList');
      if (!list) return;
      const row = document.createElement('div');
      row.className = `live-feed-item ${type}`;
      row.innerHTML = `
        <span class="live-feed-tag">[${tag}]</span>
        <time>${new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}</time>
        <strong>${company}</strong>
        <p>${message}</p>
      `;
      list.prepend(row);
      while (list.children.length > 7) list.lastElementChild.remove();
    },

    mountCarbonTopology() {
      const strip = document.querySelector('#demo-carbon .carbon-method-strip');
      if (!strip || document.getElementById('carbonTopologyCard')) return;
      const card = document.createElement('section');
      card.id = 'carbonTopologyCard';
      card.className = 'carbon-topology-card';
      card.innerHTML = `
        <div class="carbon-topology-copy">
          <span class="insight-kicker">Carbon Footprint Topology</span>
          <h4>碳足迹实时拓扑图</h4>
          <p>用“采购端 → 生产环节 → Scope 排放”的流向关系替代黑色粒子展示，让核算逻辑更直观。</p>
        </div>
        <div id="carbonTopologyChart" class="carbon-topology-chart"></div>
      `;
      strip.insertAdjacentElement('afterend', card);

      const legacy3d = document.getElementById('factory3dContainer')?.closest('.col-12');
      if (legacy3d) {
        legacy3d.classList.add('legacy-3d-retained');
        legacy3d.insertAdjacentHTML('beforebegin', '<div class="topology-replace-note">已将主要展示切换为上方碳足迹拓扑图；原 3D 数字孪生作为辅助视图保留。</div>');
      }

      if (typeof echarts === 'undefined') return;
      const chart = echarts.init(document.getElementById('carbonTopologyChart'));
      chart.setOption({
        tooltip: { trigger: 'item' },
        series: [{
          type: 'sankey',
          nodeAlign: 'justify',
          draggable: false,
          emphasis: { focus: 'adjacency' },
          data: [
            '外购电力', '柴油燃料', '物流运输', '包装耗材',
            '采购端', '生产环节', '仓储配送', 'Scope 1', 'Scope 2', 'Scope 3', '总碳排',
          ].map(name => ({ name })),
          links: [
            ['外购电力', '采购端', 42], ['柴油燃料', '采购端', 18], ['物流运输', '仓储配送', 26],
            ['包装耗材', '仓储配送', 14], ['采购端', '生产环节', 60], ['生产环节', 'Scope 1', 18],
            ['生产环节', 'Scope 2', 42], ['仓储配送', 'Scope 3', 40], ['Scope 1', '总碳排', 18],
            ['Scope 2', '总碳排', 42], ['Scope 3', '总碳排', 40],
          ].map(([source, target, value]) => ({ source, target, value })),
          lineStyle: { color: 'gradient', curveness: 0.48, opacity: 0.42 },
          itemStyle: { borderColor: '#fff', borderWidth: 1 },
          label: { color: '#172033', fontWeight: 700 },
        }],
        color: ['#1f6b4f', '#5e748c', '#b7791f', '#0f766e', '#2563eb', '#334155'],
      });
      this.topologyChart = chart;
    },

    mountEvidenceNarrative() {
      const panel = document.getElementById('evidencePanel');
      if (!panel || document.getElementById('evidenceTraceabilityCard')) return;
      const card = document.createElement('section');
      card.id = 'evidenceTraceabilityCard';
      card.className = 'evidence-traceability-card';
      card.innerHTML = `
        <div class="trace-header">
          <div>
            <span class="insight-kicker">Carbon Chain Traceability</span>
            <h4>碳链溯源系统</h4>
          </div>
          <div class="trace-stats">
            <span>链上状态<strong>已同步</strong></span>
            <span>共识节点<strong>12/12</strong></span>
            <span>最新块<strong>20,421</strong></span>
          </div>
        </div>
        <div class="trace-body">
          <div class="trace-cert">
            <span>VERIFIED ON CHAIN</span>
            <i class="fas fa-certificate"></i>
          </div>
          <div class="trace-timeline">
            <div class="trace-step done"><strong>数据原始采集</strong><span>上传电费账单，生成原始凭证哈希</span></div>
            <div class="trace-step done"><strong>AI 交叉校验通过</strong><span>OCR 字段与历史趋势匹配，共识节点确认</span></div>
            <div class="trace-step active"><strong>智能合约触发</strong><span>绿色信贷风控评分自动生成 A 级建议</span></div>
            <div class="trace-step done"><strong>链上存证完成</strong><span>Merkle Root 与时间戳已写入证据链</span></div>
          </div>
        </div>
        <button type="button" class="trace-verify-btn" data-real-mode-run>全流程核查 Verify on Chain</button>
      `;
      panel.insertAdjacentElement('beforebegin', card);
    },
  };

  window.HomeDynamics = HomeDynamics;
  document.addEventListener('DOMContentLoaded', () => HomeDynamics.init());
})();
