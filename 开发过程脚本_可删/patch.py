import re
with open('demo-flow.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Instead of strict regex, let's just find and replace the whole catch block simply
start_str = "catch (error) {\n            console.error('AI报告生成失败:', error);\n            alert(\"请求后端失败，将使用本地兜底展示。\");\n        }"
new_catch = '''catch (error) {
            console.error('大模型生成报告失败或超时，自动降级为演示数据:', error);
            if(typeof showToast === 'function') showToast('大模型调用超时，已自动加载离线演示报告', 'warning');
            await new Promise(resolve => setTimeout(resolve, 800)); // 模拟Loading
            
            DemoState.reportResult = {
                summary: 经平台核算，贵司本期总碳排放为 <strong> 吨</strong>，数据已通过区块链存证验真。(由于超时转本地演示)
            };
            
            document.getElementById('reportResultBox').style.display = 'block';
            document.getElementById('reportSummaryText').innerHTML = DemoState.reportResult.summary;
            document.getElementById('reportSuggestionList').innerHTML = <li class="mb-2"><i class="fas fa-lightbulb text-warning me-2"></i>建议在制造车间顶部安装 50kW 分布式光伏，预计年减排 15% (演示)</li><li class="mb-2"><i class="fas fa-lightbulb text-warning me-2"></i>优化空压机变频运行策略 (演示)</li>;
        }'''
    
if start_str in content:
    content = content.replace(start_str, new_catch)
else:
    # Try normalizing newlines
    c2 = content.replace('\r\n', '\n')
    if start_str in c2:
        content = c2.replace(start_str, new_catch)
    else:
        print("String not found!")

with open('demo-flow.js', 'w', encoding='utf-8') as f:
    f.write(content)
