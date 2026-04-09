import re

with open('demo-flow.js', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(
    r"summary:\s*经平台核算，贵司本期总碳排放为 <strong>[^<]*行业平均[^<]*吨</strong>，数据已通过区块链存证验真。[^\n]*",
    r"summary: `经平台核算，贵司本期总碳排放为 <strong>${DemoState.carbonResult && DemoState.carbonResult.total_emissions ? DemoState.carbonResult.total_emissions : 7.26} 吨</strong>，数据已通过区块链存证验真。(演示文本)`,", text)

text = re.sub(
    r"summary: 经平台核算，贵司本期总碳排放为 <strong> 吨</strong>，数据已通过区块链存证验真。\([^)]*\),",
    r"summary: `经平台核算，贵司本期总碳排放为 <strong>${DemoState.carbonResult && DemoState.carbonResult.total_emissions ? DemoState.carbonResult.total_emissions : 7.26} 吨</strong>，数据已通过区块链存证验真。(由于超时或无网，转演示文本)`,", text)


with open('demo-flow.js', 'w', encoding='utf-8') as f:
    f.write(text)
