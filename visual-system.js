(function () {
    const palette = {
        green: '#1F6B4F',
        greenDark: '#174F3B',
        greenSoft: '#E8F3EE',
        blueGray: '#5E748C',
        slate: '#2F4F46',
        amber: '#B7791F',
        red: '#B54747',
        text: '#1F2937',
        muted: '#6B7280',
        line: '#E5E7EB',
        panel: '#FFFFFF'
    };

    const chartColors = [
        palette.green,
        palette.blueGray,
        '#76A98E',
        palette.amber,
        palette.slate,
        '#9BB6C8',
        palette.red
    ];

    function deepMerge(target, source) {
        if (!source || typeof source !== 'object') return target;
        Object.keys(source).forEach(key => {
            const value = source[key];
            if (Array.isArray(value)) {
                target[key] = value;
            } else if (value && typeof value === 'object') {
                target[key] = deepMerge(target[key] && typeof target[key] === 'object' ? target[key] : {}, value);
            } else if (target[key] === undefined) {
                target[key] = value;
            }
        });
        return target;
    }

    function axisDefaults(axis) {
        if (!axis) return axis;
        const list = Array.isArray(axis) ? axis : [axis];
        list.forEach(item => {
            item.axisLine = deepMerge(item.axisLine || {}, { lineStyle: { color: '#D9E1E5' } });
            item.axisTick = deepMerge(item.axisTick || {}, { show: false });
            item.axisLabel = deepMerge(item.axisLabel || {}, { color: palette.muted, fontSize: 12, margin: 10 });
            item.splitLine = deepMerge(item.splitLine || {}, { lineStyle: { color: '#EDF1F3', type: 'dashed' } });
            item.nameTextStyle = deepMerge(item.nameTextStyle || {}, { color: palette.muted, fontSize: 12, padding: [0, 0, 0, 4] });
        });
        return axis;
    }

    function polishSeries(series) {
        const list = Array.isArray(series) ? series : (series ? [series] : []);
        list.forEach((item, index) => {
            item.animationDuration = item.animationDuration || 900;
            item.animationEasing = item.animationEasing || 'cubicOut';
            item.itemStyle = deepMerge(item.itemStyle || {}, {
                borderRadius: item.type === 'bar' ? [4, 4, 0, 0] : 0
            });
            if (item.type === 'line') {
                item.smooth = item.smooth !== undefined ? item.smooth : true;
                item.symbol = item.symbol || 'circle';
                item.symbolSize = item.symbolSize || 7;
                item.lineStyle = deepMerge(item.lineStyle || {}, { width: 3 });
                item.areaStyle = item.areaStyle || {
                    opacity: 0.08,
                    color: chartColors[index % chartColors.length]
                };
            }
            if (item.type === 'pie') {
                item.radius = item.radius || ['48%', '72%'];
                item.label = deepMerge(item.label || {}, { color: palette.text, fontSize: 12 });
                item.itemStyle = deepMerge(item.itemStyle || {}, {
                    borderColor: '#FFFFFF',
                    borderWidth: 3
                });
            }
            if (item.type === 'radar') {
                item.lineStyle = deepMerge(item.lineStyle || {}, { width: 3 });
                item.areaStyle = item.areaStyle || { opacity: 0.09 };
            }
        });
    }

    function polishOption(option) {
        if (!option || typeof option !== 'object') return option;
        option.color = option.color || chartColors;
        option.backgroundColor = option.backgroundColor || 'transparent';
        option.textStyle = deepMerge(option.textStyle || {}, {
            color: palette.text,
            fontFamily: '"Microsoft YaHei UI", "Microsoft YaHei", sans-serif'
        });
        option.tooltip = deepMerge(option.tooltip || {}, {
            trigger: option.tooltip?.trigger || 'axis',
            backgroundColor: 'rgba(255, 255, 255, 0.96)',
            borderColor: '#DDE7E1',
            borderWidth: 1,
            padding: [10, 12],
            textStyle: { color: palette.text, fontSize: 12 },
            extraCssText: 'box-shadow:0 12px 28px rgba(31,41,55,.14);border-radius:8px;'
        });
        option.legend = deepMerge(option.legend || {}, {
            top: 8,
            right: 12,
            icon: 'roundRect',
            itemWidth: 12,
            itemHeight: 8,
            textStyle: { color: palette.muted, fontSize: 12 }
        });
        option.grid = deepMerge(option.grid || {}, {
            left: 46,
            right: 28,
            top: 58,
            bottom: 36,
            containLabel: true
        });
        option.xAxis = axisDefaults(option.xAxis);
        option.yAxis = axisDefaults(option.yAxis);
        if (option.radar) {
            option.radar = deepMerge(option.radar, {
                axisName: { color: palette.muted, fontSize: 12 },
                splitLine: { lineStyle: { color: '#E9EEF0' } },
                splitArea: { areaStyle: { color: ['rgba(31,107,79,0.03)', 'rgba(255,255,255,0.65)'] } },
                axisLine: { lineStyle: { color: '#DDE7E1' } }
            });
        }
        polishSeries(option.series);
        return option;
    }

    function installEChartsTheme() {
        if (!window.echarts || window.__carbonVisualEchartsInstalled) return;
        window.__carbonVisualEchartsInstalled = true;

        echarts.registerTheme('carbon-premium', {
            color: chartColors,
            backgroundColor: 'transparent',
            textStyle: { color: palette.text },
            title: { textStyle: { color: palette.text, fontWeight: 700 }, subtextStyle: { color: palette.muted } }
        });

        const originalInit = echarts.init;
        echarts.init = function (dom, theme, opts) {
            const chart = originalInit.call(echarts, dom, theme || 'carbon-premium', opts);
            const originalSetOption = chart.setOption;
            chart.setOption = function (option) {
                if (option && !option.__carbonPolished) {
                    polishOption(option);
                    Object.defineProperty(option, '__carbonPolished', { value: true, enumerable: false });
                }
                return originalSetOption.apply(chart, arguments);
            };
            return chart;
        };
    }

    function installChartDefaults() {
        if (!window.Chart || window.__carbonVisualChartInstalled) return;
        window.__carbonVisualChartInstalled = true;
        Chart.defaults.color = palette.muted;
        Chart.defaults.font.family = '"Microsoft YaHei UI", "Microsoft YaHei", sans-serif';
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.boxWidth = 8;
        Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(255,255,255,.96)';
        Chart.defaults.plugins.tooltip.titleColor = palette.text;
        Chart.defaults.plugins.tooltip.bodyColor = palette.text;
        Chart.defaults.plugins.tooltip.borderColor = '#DDE7E1';
        Chart.defaults.plugins.tooltip.borderWidth = 1;
        Chart.defaults.plugins.tooltip.padding = 12;
        Chart.defaults.elements.arc.borderColor = '#FFFFFF';
        Chart.defaults.elements.arc.borderWidth = 3;
        Chart.defaults.datasets.doughnut.backgroundColor = chartColors;
        Chart.defaults.datasets.pie.backgroundColor = chartColors;
    }

    function installModalGuard() {
        if (window.__carbonVisualModalGuardInstalled) return;
        window.__carbonVisualModalGuardInstalled = true;

        document.addEventListener('show.bs.modal', event => {
            const modal = event.target;
            if (modal && modal.parentElement !== document.body) {
                document.body.appendChild(modal);
            }
        });

        document.addEventListener('hidden.bs.modal', () => {
            if (!document.querySelector('.modal.show')) {
                document.querySelectorAll('.modal-backdrop').forEach(backdrop => backdrop.remove());
                document.body.classList.remove('modal-open');
                document.body.style.removeProperty('overflow');
                document.body.style.removeProperty('padding-right');
            }
        });
    }

    window.CarbonVisualSystem = {
        palette,
        chartColors,
        polishOption,
        install() {
            installEChartsTheme();
            installChartDefaults();
            installModalGuard();
        }
    };

    window.CarbonVisualSystem.install();
})();
