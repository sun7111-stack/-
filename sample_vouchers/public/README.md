# 公开样例票据说明

这个目录用于替换“排放因子查询表”作为 OCR/真实闭环演示材料。排放因子表是核算参数，不是企业活动凭证；真实闭环更适合上传电费账单、燃气账单、油票、物流运单、发票等凭证。

## 推荐演示文件

| 文件 | 类型 | 推荐用途 | 当前解析结果 |
| --- | --- | --- | --- |
| `pucn_sample_electric_bill.pdf` | 电费账单 | 自动化碳核算主演示 | 可解析 `350 kWh` |
| `pucn_sample_gas_bill.pdf` | 天然气账单 | Scope 1 / 燃气场景 | 可解析 `88 therm` |
| `gov_cn_vat_e_invoice_sample.pdf` | 官方电子发票票样 | 发票 OCR 版式参考 | 可识别为发票票样，不建议直接做碳核算活动量 |
| `epa_sample_electric_bill.pdf` | 电费账单说明样例 | 版式参考 | 文档较复杂，当前简单规则可能抓到非核心 kWh 数值 |

## 来源

- EPA sample electric bill: https://www.epa.gov/sites/default/files/2015-06/documents/sample-elec-bill.pdf
- PUC Nevada sample electric bill: https://puc.nv.gov/uploadedFiles/pucnvgov/Content/Utilities/MHP/SampleElectricBill.pdf
- PUC Nevada sample gas bill: https://puc.nv.gov/uploadedFiles/pucnvgov/Content/Utilities/MHP/SampleGasBill.pdf
- 中国政府网增值税电子专用发票票样附件: https://www.gov.cn/zhengce/zhengceku/2020-12/21/5571923/files/0f2ec1eae0d842b1b70650f95631767c.pdf

## 使用建议

1. 首页 Real Mode 面板中选择“可选上传票据”。
2. 优先上传 `pucn_sample_electric_bill.pdf`。
3. 点击“运行真实闭环”。
4. 如果只想测试 OCR，进入“上传识别”页面上传同一文件。
5. 不要再用“主要能源碳排放因子查询表”作为票据，它应该进入因子库，而不是 OCR 票据流。

## 隐私说明

不要从网上随便下载个人真实账单、企业发票或物流单据。真实票据往往包含姓名、地址、税号、账号、联系方式等敏感信息。演示和答辩建议使用公开样例、官方票样或脱敏后的企业内部样例。
