with open("demo-flow.js", "r", encoding="utf-8") as f:
    content = f.read()

# Fix carbonTotalCard display logic
content = content.replace("document.getElementById('carbonTotalCard').style.display = 'block';", "document.getElementById('carbonTotalCard').style.display = 'flex';")

# Need to render Pie Chart
pie_chart_code = """
  // Initialize Pie chart inside breakdown
  function renderPieChart() {
      const pieDom = document.getElementById('pieChartBox');
      if (!pieDom) return;
      const pieChart = echarts.init(pieDom);
      const pieOption = {
          tooltip: { trigger: 'item' },
          legend: { top: '5%', left: 'center', itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
          series: [
              {
                  name: '排放来源',
                  type: 'pie',
                  radius: ['40%', '70%'],
                  avoidLabelOverlap: false,
                  itemStyle: {
                      borderRadius: 10,
                      borderColor: '#fff',
                      borderWidth: 2
                  },
                  label: { show: false, position: 'center' },
                  emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
                  labelLine: { show: false },
                  data: [
                      { value: 3.12, name: '电力排放(3.12)', itemStyle: { color: '#2E7D32' } },
                      { value: 1.48, name: '运输排放(1.48)', itemStyle: { color: '#F9A825' } },
                      { value: 1.87, name: '燃料排放(1.87)', itemStyle: { color: '#0277BD' } },
                      { value: 0.79, name: '其他排放(0.79)', itemStyle: { color: '#757575' } }
                  ]
              }
          ]
      };
      pieChart.setOption(pieOption);
  }
"""

if "renderPieChart()" not in content:
    content = content.replace("function renderBenchmarkChart(currentValue) {", pie_chart_code + "\n  function renderBenchmarkChart(currentValue) {")
    content = content.replace("renderBenchmarkChart(total);", "renderBenchmarkChart(total);\n              if(typeof renderPieChart === 'function') renderPieChart();")
    content = content.replace("renderBenchmarkChart(total);", "renderBenchmarkChart(total);\n       if(typeof renderPieChart === 'function') renderPieChart();")

with open("demo-flow.js", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated demo-flow.js logic for charts.")
