# 碳核算引擎 API 接口联调协议 (API CONTRACT)

这份协议是 3号同学（碳核算引擎）向 1号(前端)、2号(OCR/视觉) 和 4号(风控/大模型分析) 提供的接口格式与约定。

---

## 1. 与 2 号同学（OCR / VLM）对接约定

### 1-1 活动类型枚举约定
为了保证传入后能够精准匹配到底层碳排放因子，2号同学在将 OCR 解析出的表单映射时，`suggested_activity_type` 必须从以下核心枚举值中产生：
- `electricity` : 电力/电费单
- `natural_gas`: 天然气单据
- `diesel` : 柴油采购单
- `air_logistics` : 航空物流单
- `warehouse_energy` : 仓储能耗账单
- `reverse_logistics` : 逆向物流/退货单
- `packaging_waste` : 包装废弃物工单
- `waste` : 普通废弃物单据

### 1-2 `fields` 字段传值规范约定
对于 OCR 抽取出的零散字段结构 `fields`，请尽量提供明确且可解析的数字。引擎侧在缺失直构数据时会执行退化匹配（即搜寻内部的第一个纯数字字段），为了保证稳定，建议确保：
- **电费单等能源单据**：必须含有 `amount` 字段（数字，如用电度数）
- **物流账单**：尽量包括 `distance`（距离）或 `weight`（重量）。

---

## 2. 与 4 号同学（智能风控 / AI 报告）对接约定

引擎侧最终生成的响应实体中，这些核心字段**具有绝对稳定的层级**，供下游进行评级与诊断计算。

```json
{
  "total_emission": 2850.4,           // 您的风控可以直接应用这个作为企业碳排标尺
  "breakdown": [                      // AI 诊断报告素材极佳来源
    {
      "item": "electricity",
      "amount": 1245.0,
      "factor": 0.5703,
      "emission": 710.0,
      "unit": "kgCO2e/kWh",
      "source": "生态环境部2022年全国..." // 生成报告可直接引用，增强可信度
    }
  ],
  "benchmark_compare": {
    "industry_avg": 3100.0,
    "deviation_ratio": -0.081,        // 可用作环境评分 (Esg Score) 的挂载依据
    "position": "低于行业平均 8.1%",
    "rank_label": "良好",
    "carbon_intensity": 2.8504        // 碳排强度 = 总量/营收
  }
}
```

---

## 3. 与 1 号同学（前端大屏展示）对接约定

前端在调用 `/api/carbon/calculate` 后可以完全依赖这个返回值渲染大屏和看板：
1. **碳排大数**：直接取 `total_emission`
2. **位置对标挂件**：使用 `benchmark_compare.industry_avg` 渲染横条进度，`position` 字段供高亮说明文字直接展示。（不用额外算偏移百分比）
3. **分项饼图 (Pie Chart)**：直接遍历 `breakdown` 数组中的 `item` 和 `emission`。
