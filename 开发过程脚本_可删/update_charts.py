import re

with open('demo-flow.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update initDashboardDemo
new_init_dashboard = '''function initDashboardDemo() {
    const chartDom = document.getElementById('dashboardDemo');
    if (!chartDom) return;
    const chart = echarts.init(chartDom);
    
    // Default fallback options
    const fallbackOption = {
        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
        toolbox: { feature: { magicType: { show: true, type: ['line', 'bar'] }, saveAsImage: { show: true } } },
        legend: { data: ['碳排放量', '行业平均'], top: 10 },
        xAxis: [{ type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月'] }],
        yAxis: [{ type: 'value', name: '吨(t)' }],
        series: [
            { name: '碳排放量', type: 'bar', data: [15, 20, 22, 18, 25, 24], itemStyle: { color: '#4CAF50' } },
            { name: '行业平均', type: 'line', data: [18, 22, 23, 20, 26, 26], itemStyle: { color: '#FF9800' } }
        ]
    };
    
    chart.setOption(fallbackOption); // Initial render with structural skeleton

    // 真正的请求
    API.request('/dashboard/emission-monitor').then(res => {
        if (res && res.months) {
            chart.setOption({
                xAxis: [{ data: res.months }],
                series: [
                    { name: '碳排放量', data: res.company_emissions },
                    { name: '行业平均', data: res.industry_average }
                ]
            });
        }
    }).catch(err => {
        console.error('加载 Dashboard 真实数据超时或失败，已自动展示演示沙盒图表：', err);
    });

    window.addEventListener('resize', () => chart.resize());
}'''

content = re.sub(r'function initDashboardDemo\(\)\s*\{[\s\S]*?window\.addEventListener\(\'resize\',\s*\(\)\s*=>\s*\{\s*chart\.resize\(\);\s*\}\);\s*\}', new_init_dashboard, content)

# 2. Update initESGRadarChart
new_radar_chart = '''function initESGRadarChart() {
    const chartDom = document.getElementById('esgRadarChart');
    if (!chartDom) return;
    const chart = echarts.init(chartDom);
    
    const fallbackOption = {
        tooltip: { trigger: 'item' },
        radar: {
            indicator: [
                { name: '环境治理 (E)', max: 100 },
                { name: '社会责任 (S)', max: 100 },
                { name: '公司治理 (G)', max: 100 },
                { name: '能效管理', max: 100 },
                { name: '碳排控制', max: 100 }
            ]
        },
        series: [{
            type: 'radar',
            data: [
                { value: [75, 80, 85, 70, 90], name: '当前表现 (演示)', itemStyle: { color: '#4CAF50' }, areaStyle: { color: 'rgba(76, 175, 80, 0.3)' } },
                { value: [60, 65, 70, 60, 75], name: '行业平均', lineStyle: { type: 'dashed' }, itemStyle: { color: '#FF9800' } }
            ]
        }]
    };
    
    chart.setOption(fallbackOption); // 先挂载骨架
    
    API.request('/dashboard/esg-board').then(res => {
        if (res && res.scores) {
            chart.setOption({
                radar: {
                    indicator: res.dimensions.map(d => ({ name: d, max: 100 }))
                },
                series: [{
                    data: [
                        { value: res.scores, name: '企业真实表现', itemStyle: { color: '#4CAF50' }, areaStyle: { color: 'rgba(76, 175, 80, 0.3)' } },
                        { value: res.industry_scores || fallbackOption.series[0].data[1].value, name: '行业基准', lineStyle: { type: 'dashed' }, itemStyle: { color: '#FF9800' } }
                    ]
                }]
            });
        }
    }).catch(err => {
        console.error('加载 ESG 波浪雷达图真实数据失败，自动退回演示沙盒状态:', err);
    });

    window.addEventListener('resize', () => chart.resize());
}'''

content = re.sub(r'function initESGRadarChart\(\)\s*\{[\s\S]*?window\.addEventListener\(\'resize\',\s*\(\)\s*=>\s*\{\s*chart\.resize\(\);\s*\}\);\s*\}', new_radar_chart, content)

with open('demo-flow.js', 'w', encoding='utf-8') as f:
    f.write(content)
