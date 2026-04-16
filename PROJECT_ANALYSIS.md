# 碳排放计算项目 - 代码结构分析

## 项目概览
- **项目名称**：碳融智核 (Carbon-emission-calculation)
- **主要技术栈**：FastAPI(后端) + HTML/JS(前端)
- **核心功能**：企业碳排放核算、ESG评分、风险检测、AIGC报告生成、OCR票据识别
- **时间**：2025年演示版本

---

## 1️⃣ REPORT_LLM 当前实现

### 📁 核心文件
| 路径 | 说明 |
|------|------|
| [backend/services/report_llm.py](backend/services/report_llm.py) | **LLM报告生成模块** - 调用DashScope API核心逻辑 |
| [backend/routers/reports.py](backend/routers/reports.py) | 报告路由 - 与前端API对接 |
| [backend/schemas/report.py](backend/schemas/report.py) | 报告数据模型 |
| [backend/config.py](backend/config.py) | DashScope API配置 |

### 🎯 关键类和函数

#### `CarbonReportGenerator` 类
```python
# 初始化
- __init__()
  └─ _init_dashscope()  # 初始化DashScope客户端

# 核心方法
- generate(ReportInputData) → ReportOutputData
  ├─ _build_prompt()        # 构建Prompt（用户输入或模板）
  ├─ _call_qwen()          # 调用Qwen模型（真实API）
  └─ _mock_report()        # 降级Mock方案

- _build_prompt(body)
  └─ 拼接：企业名、周期、排放指标、ESG分、风控结果、排放分项、建议模板
```

### 📋 输入数据模型 (`ReportInputData`)
```python
{
  company_name: str              # "Demo企业"
  period: str                    # "本期"
  total_emission: float          # 总排放(tCO2e)
  carbon_intensity: float        # 碳强度(t/万元)
  industry_avg_intensity: float  # 行业对标
  emission_breakdown: List[Dict] # [{"source": "电力", "value": 100}]
  risk_result: Dict              # {"risk_level": "medium", ...}
  esg_score: float               # 75.0
  prompt: Optional[str]          # 用户自定义问题
}
```

### 📤 输出数据模型 (`ReportOutputData`)
```python
{
  report_text: str      # 生成的富文本报告
  is_mock: bool         # 是否为Mock（无Key或API失败时为True）
  model_used: str       # "Qwen" 或 "Mock Engine v1.0"
}
```

### 🔌 API调用细节
**DashScope API调用**：
```python
dashscope.Generation.call(
    model="qwen-plus",
    prompt="<构建的完整Prompt>",
    max_tokens=1500,
    temperature=0.6,
    top_p=0.8
)
```

**调用时机**：
- ✅ 有DASHSCOPE_API_KEY → 调用真实API
- ❌ 无Key或引入失败 → 自动降级Mock

### 🛣️ API路由
**POST** `/api/reports/generate` - 生成报告
- 接收 `ReportGenerate` (template_type, title, scenario)
- 返回 `ReportOut` (id, title, status, word_count, charts_count)
- ⚠️ **注意**：当前路由返回的是数据库Report对象，未调用LLM

---

## 2️⃣ 分析服务数据流

### 📁 核心文件
| 路径 | 说明 |
|------|------|
| [backend/models/analysis.py](backend/models/analysis.py) | **核算结果模型** - AnalysisResult |
| [backend/models/analysis_v2.py](backend/models/analysis_v2.py) | V2快照模型 - AnalysisResultV2Snapshot |
| [backend/routers/risk.py](backend/routers/risk.py) | 风控路由 - 风险检测流程 |
| [backend/services/risk_detector.py](backend/services/risk_detector.py) | Isolation Forest异常检测 |
| [backend/services/carbon_engine/](backend/services/carbon_engine/) | 碳核算引擎 |

### 📊 数据模型详解

#### `AnalysisResult` 表（核算结果）
```python
class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    # 基本信息
    id: int PK
    user_id: int FK → users.id
    enterprise_name: str(200)
    analysis_time: DateTime
    
    # 核算结果
    total_emission: float          # ✅ 总排放量(tCO2e)
    carbon_intensity: float        # ✅ 碳强度(t/万元)
    industry_deviation: float      # 行业偏差
    
    # Scope分布（关键字段）⭐
    scope1: float                  # ✅ 范围1-直接排放(kgCO2e)
    scope2: float                  # ✅ 范围2-外购能源(kgCO2e)
    scope3: float                  # ✅ 范围3-价值链排放(kgCO2e)
    
    # 不确定性分析
    ci95_low: float                # 下界(95%置信)
    ci95_high: float               # 上界(95%置信)
    uncertainty_mode: str(20)      # "analytic"/"monte_carlo"
    
    # 风险与建议
    risk_level: str(30)            # "low"/"medium"/"high"
    major_source: str(100)         # 主要排放源
    top_contributor_activity_id: int  # 最大贡献activity_id
    advice_text: Text              # AI建议文本
```

#### `AnalysisBreakdown` 表（排放分解）
```python
class AnalysisBreakdown(Base):
    __tablename__ = "analysis_breakdowns"
    
    id: int PK
    analysis_id: int FK → analysis_results.id
    source_type: str(80)          # "电力"/"天然气"/"物流"等
    emission_value: float         # 排放量
    proportion: float             # 占比%
```

#### `AnalysisResultV2Snapshot` 表（V2快照）⭐ 新增
```python
class AnalysisResultV2Snapshot(Base):
    __tablename__ = "analysis_result_v2_snapshot"
    
    id: int PK
    analysis_id: int FK
    model_version: str
    uncertainty_mode: str
    
    # 关键富数据
    scope_breakdown: JSON          # ✅ {"scope1": 100, "scope2": 200, ...}
    source_breakdown: JSON         # ✅ [{"source": "电力", "value": 200}]
    uncertainty: JSON              # {"ci95": [95, 105], "samples": 10000}
    top_contributors: JSON         # 排放TOP N源
    factor_trace: JSON             # 因子选用追溯
    carbon_flow_graph: JSON        # 流向图数据
    explain_trace: JSON            # 解释链路
```

#### `RiskResult` 表（风控结果）
```python
class RiskResult(Base):
    __tablename__ = "risk_results"
    
    id: int PK
    user_id: int FK
    analysis_id: int FK (nullable)
    
    risk_score: float              # 0-100风险评分
    risk_level: str(30)            # "low"/"medium"/"high"
    risk_reason: Text              # 风险原因(AI生成)
    risk_advice: Text              # 风险建议
    created_at: DateTime
```

### 🔬 风险检测流程 (`RiskDetector`)

#### 输入数据
```python
class RiskInputData:
    electricity_usage: float        # kWh
    logistics_distance: float       # km
    return_rate: float              # %
    total_emission: float           # tCO2e
    carbon_intensity: float         # t/万元
```

#### 检测方法
```python
class IsolationForestRiskDetector:
    def detect(input_data) → RiskOutputData:
        ├─ 特征归一化：[electricity, logistics, return_rate, emission, intensity]
        ├─ Isolation Forest预测：predict() + score_samples()
        ├─ 异常判断：anomaly_label == -1 OR risk_score > 60
        ├─ 异常标签生成：
        │  ├─ 用电 > 15000 kWh → "用电量异常偏高"
        │  ├─ 物流 > 30000 km → "物流距离异常偏长"
        │  ├─ 退货率 > 30% → "退货率异常偏高"
        │  └─ 碳强度 > 1.5 → "碳强度显著高于行业"
        └─ 风险评分：(1 - anomaly_score) / 2 * 100
```

#### 综合风险评分（多维度）
```python
# 三维风险评分
carbon_risk = Isolation Forest异常分数        # Rc
esg_risk = 100 - esg_score                   # Re (缺省75分)
governance_risk = return_rate * 100 + carbon_intensity * 20  # Rg

# 综合评分函数
explain_score_v2 = 
    0.45 * carbon_risk +
    0.35 * esg_risk +
    0.15 * governance_risk +
    0.05 * (1 - trust_score) * 100
```

#### 风险等级分类
```python
def classify_risk_level(score):
    if score < 25: return "low"
    elif score < 50: return "medium"
    else: return "high"
```

### 🛣️ 核心API路由

| 方法 | 路由 | 说明 |
|------|------|------|
| **POST** | `/api/risk/detect` | Isolation Forest风控检测 |
| **POST** | `/api/reports/generate` | 生成报告 |
| **GET** | `/api/reports/templates` | 获取报告模板列表 |
| **GET** | `/api/reports` | 报告历史 |

---

## 3️⃣ 前端UI接入点

### 📁 前端文件
| 路径 | 说明 |
|------|------|
| [index.html](index.html) | **主UI页面** - 完整HTML结构 |
| [demo-flow.js](demo-flow.js) | **交互逻辑** - 4大核心流程 |
| [script.js](script.js) | 备用脚本 |
| [style.css](style.css) | 样式 |

### 🎯 核心UI组件位置（index.html）

#### 1️⃣ OCR票据识别模块
```html
<!-- L260: 菜单项 -->
<li data-page="demo-upload">
    <a href="#demo-upload">票据智能识别</a>

<!-- L501-510: 功能描述和按钮 -->
<button data-bs-toggle="modal" data-bs-target="#ocrDemoModal">
    OCR演示

<!-- L1853-1890: Modal弹窗（内含文件上传&结果展示） -->
<div id="ocrDemoModal">
    <div id="uploadArea">                <!-- 拖拽上传区域 -->
    <div id="ocrResult">                <!-- 识别结果容器 -->
```

#### 2️⃣ 风险评分模块
```html
<!-- L272: 菜单项 -->
<li data-page="demo-risk">
    <a href="#demo-risk">风险评分</a>

<!-- L1009-1015: 风险输入表单 -->
<div class="risk-inputs">
    <select id="riskManagement">        <!-- 风险项选择 -->

<!-- L2187: 按钮绑定（demo-flow.js） -->
function bindRiskButton()
```

#### 3️⃣ 报告生成模块
```html
<!-- L278: 菜单项 -->
<li data-page="demo-report">
    <a href="#demo-report">报告生成</a>

<!-- L1094-1160: 报告UI容器 -->
<div class="report-types">
    <div class="report-type-card" data-type="carbon">    <!-- 碳报告 -->
    <div class="report-type-card" data-type="esg">      <!-- ESG报告 -->
    <div class="report-type-card" data-type="finance">  <!-- 金融报告 -->

<div class="report-generator">
    <div class="report-templates">
        <button onclick="generateReport('basic')">     <!-- 基础报告 -->
        <button onclick="generateReport('reduction')">  <!-- 减排报告 -->
        <button onclick="generateReport('esg')">        <!-- ESG报告 -->

    <div id="reportPreview">                            <!-- 报告预览区 -->

<!-- L1167-1175: 报告操作按钮 -->
<button onclick="downloadReport()">下载报告</button>
<button onclick="shareReport()">分享报告</button>
<button onclick="saveToCloud()">保存至云端</button>
```

#### 4️⃣ 数据上传与处理
```html
<!-- L260-261: 上传菜单 -->
<li class="menu-item" data-page="demo-upload">
    <a href="#demo-upload">票据上传</a>

<!-- L346: 工具栏上传按钮 -->
<button class="tool-btn" data-bs-toggle="modal" data-bs-target="#reportModal">
    报告生成
```

### 🔗 前端-后端API调用栈（demo-flow.js）

#### 核心入口
```javascript
// L1899 - 初始化
function initDemoFlow() {
    ├─ bindRecognizeButton()        // OCR识别按钮
    ├─ bindCarbonButton()           // 碳核算按钮
    ├─ bindRiskButton()             // 风险评分按钮
    └─ bindReportButton()           // 报告生成按钮
}
```

#### 4大核心流程控制函数

| 函数 | 行号 | 功能 | 后端接口 |
|------|------|------|---------|
| `bindRecognizeButton()` | 2252+ | OCR识别 → 文件上传 | `POST /api/ocr/recognize` |
| `bindCarbonButton()` | 2269+ | 碳核算 → 排放量计算 | `POST /api/carbon/calculate` (未实装) |
| `bindRiskButton()` | 2187+ | 风险检测 → Isolation Forest | `POST /api/risk/detect` |
| `bindReportButton()` | 2654+ | 报告生成 → LLM调用 | `POST /api/reports/generate` |

#### 状态管理
```javascript
// L2100+ DataService - 数据字典
- reportTemplates      // 报告模板配置
- emissionFactors      // 排放因子库
- industriyBenchmarks  // 行业基准
- financialProducts    // 金融产品

// PlatformState - 应用状态
- user                 // 当前用户
- esgScore             // ESG分数
- reportHistory        // 报告历史
- carbonData           // 碳核算数据
```

### 📊 关键UI交互流程图
```
OCR识别 → 票据数据提取 → 碳核算计算 → 排放结果
                          ↓
                      风险评分检测(Isolation Forest)
                          ↓
                      综合指标 + ESG评分
                          ↓
                      LLM报告生成(DashScope)
                          ↓
                    下载/分享/云端保存
```

---

## 4️⃣ OCR与票据处理

### 📁 核心文件
| 路径 | 说明 |
|------|------|
| [backend/services/vlm_parser.py](backend/services/vlm_parser.py) | **VLM票据解析** - DashScope多模态API |
| [backend/routers/ocr.py](backend/routers/ocr.py) | OCR路由 - 前端接入点 |
| [backend/models/data_pipeline.py](backend/models/data_pipeline.py) | 原始数据+解析数据模型 |

### 🎯 VLM解析器核心类

#### `VLMParser` 类
```python
class VLMParser:
    @staticmethod
    def parse_document(file_obj, filename) → Dict:
        
        # 步骤1：读取文件
        content, suffix, mime_type = _read_file(file_obj, filename)
        
        # 步骤2：选择解析策略
        if USE_MOCK or not DASHSCOPE_API_KEY:
            return _parse_mock(filename)
        else:
            return _parse_llm(content, suffix, mime_type)
    
    # Mock解析（无API时自动降级）
    @staticmethod
    def _parse_mock(filename: str) → Dict:
        # 根据文件名推断票据类型
        if "电" in filename or "electricity" in filename:
            return {
                "doc_type": "electricity_bill",
                "confidence": 0.95,
                "fields": {
                    "amount": 1245,           # kWh
                    "unit": "kWh",
                    "period": "2025-03",
                    "vendor": "××电网",
                    "price": 0.6999
                }
            }
        # 其他类型...

    # 真实LLM解析（调用Qwen VLM）
    @staticmethod
    def _parse_llm(file_content, suffix, mime_type) → Dict:
        # 构造多模态消息
        if mime_type == "image":
            messages = [{
                "role": "user",
                "content": [
                    {"image": f"data:image/{suffix};base64,{encoded_bytes}"},
                    {"text": SYSTEM_PROMPT}
                ]
            }]
        else:  # PDF
            text = PdfReader提取文本
            messages = [{
                "role": "user",
                "content": [
                    {"text": f"{SYSTEM_PROMPT}\n\nPDF文本:\n{text}"}
                ]
            }]
        
        # 调用 MultiModalConversation.call()
        response = dashscope.MultiModalConversation.call(
            model="qwen-vl-max",
            messages=messages,
            stream=False
        )
        
        # 解析JSON响应
        return json.loads(_extract_json_text(response.output.text))
```

### 📋 输出数据模型

#### `OCRParseResult` (Schemas)
```python
{
    doc_type: str                  # "electricity_bill" | "logistics_bill" | "fuel_bill"
    confidence: float (0-1)        # ✅ 识别置信度 - Qwen自评
    fields: Dict                   # ✅ 结构化字段（因票据类型而异）
    raw_text: str                  # 原始OCR文本（存证用）
    suggested_activity_type: str   # "electricity"/"air_logistics"/"diesel"等
    
    # 数据管道中间结果
    raw_data: Optional[Dict]       # 原始解析数据
    parsed_data: Optional[Dict]    # 数据治理后结果
    normalized_data: Optional[Dict] # 归一化数据
    mapped_data: Optional[list]    # 映射到活动数据
    cleaned_record: Optional[Dict] # 清洗后数据
}
```

#### `RawDataRecord` (Models)
```python
# 原始凭证记录（tickets_table）
class RawDataRecord:
    data_type: str                 # "image/jpeg"
    file_name: str
    file_path: str
    parse_status: str              # "processing"/"completed"/"failed"
```

#### `ParsedDataRecord` (Models)
```python
# 解析后数据记录
class ParsedDataRecord:
    raw_data_id: int FK
    parsed_result: JSON            # Qwen返回的结构化JSON
    confidence: float              # VLM置信度
    doc_type: str
    extracted_fields: JSON
```

### 🔌 API路由

#### **POST** `/api/ocr/recognize` - 票据结构化识别
**请求**：
```python
{
    file: UploadFile (JPG/PNG/PDF, max 10MB)
}
```

**响应**：
```python
{
    success: bool,
    data: {
        doc_type: "electricity_bill",
        confidence: 0.95,                    # ← 关键：VLM评估的置信度
        fields: {
            # 因票据类型而异
            # 电费单: {amount, unit, period, vendor, price}
            # 物流单: {distance, weight, transport_type, waybill_no}
            # 燃油单: {amount, fuel_type, vendor}
        },
        suggested_activity_type: "electricity"
    }
}
```

#### **GET** `/api/ocr/health` - 健康检查
返回模式状态(Mock vs 真实API)

#### **GET** `/api/ocr/chain-check` - 数据确权链路检查
返回：raw_data → parsed_data → activity_data流程状态

### 🛡️ 失败处理流程

#### 1️⃣ 文件校验阶段
```python
# ocr.py line 79-86
if file.content_type not in SUPPORTED_TYPES:
    raise HTTPException(400, "文件格式不支持，仅支持JPG/PNG/PDF")

if len(content) > MAX_SIZE:
    raise HTTPException(400, f"文件过大，最大{MAX_SIZE}MB")
```

#### 2️⃣ VLM解析失败处理
```python
# vlm_parser.py
if not DASHSCOPE_AVAILABLE:
    raise Exception("未安装dashscope SDK")

if not DASHSCOPE_API_KEY:
    raise Exception("未配置DASHSCOPE_API_KEY")

def parse_document_wrapper(file):
    try:
        return VLMParser.parse_document(file_obj, filename)
    except Exception as e:
        # 自动降级到Mock模式
        return _parse_mock(filename)
```

#### 3️⃣ 数据治理（防护层）
```python
# ocr.py & data_governance.py
def govern_parsed_result(result_data, enterprise_id):
    # 验证必填字段、清洗特殊字符、类型转换
    # 异常数据标记为low_confidence
    return normalized_result
```

#### 4️⃣ 响应包装
```python
# ocr.py line ~100
OCRResponse(
    success: True/False,
    data: result_data or None,
    message: error_detail or "success"
)
```

### 📊 Confidence评分逻辑

#### 来源1：Qwen VLM自评
```python
# vlm_parser.py - VLM返回JSON中的confidence字段
{
    "confidence": 0.92,          # Qwen模型自评(0-1)
    "doc_type": "electricity_bill",
    "fields": {...}
}
```

#### 来源2：数据治理规则
```python
# data_governance.py
def calc_confidence_score(parsed_data):
    base_score = parsed_data.get("confidence", 0.5)
    
    # 规则调整
    if missing_required_fields:
        base_score *= 0.7
    
    if outlier_detected:
        base_score *= 0.8
    
    if field_type_mismatch:
        base_score *= 0.9
    
    return max(0, min(1, base_score))
```

#### 来源3：证据链信任度
```python
# flow.py & evidence_chain.py
def compute_trust_score(evidence_steps):
    # 基于链路完整性、时间戳有效性、数据一致性
    return trust_score (0-100)
```

### 🚨 异常处理场景

| 场景 | 处理方式 | 状态 |
|------|---------|------|
| VLM识别失败 | 降级到Mock | low_confidence |
| 文件格式错误 | 拒绝 | error |
| 字段缺失 | 标记+后续人工验证 | medium_confidence |
| 数值离群 | 标记为可疑+保留 | low_confidence |
| API超时 | 重试3次 → Mock | low_confidence |

---

## 📊 数据流完整链路

```
用户上传票据
    ↓
[OCR识别] (VLM: Qwen-VLM-Max)
    ├─ 票据类型识别 (electricity/logistics/fuel/...)
    ├─ 关键字段提取 (用量/金额/日期/...)
    └─ Confidence评分 (0.5-0.95)
    ↓
[数据治理] (Data Governance)
    ├─ 字段完整性验证
    ├─ 数值有效性检查
    ├─ 离群值检测
    └─ 后续 Confidence 调整
    ↓
[排放因子匹配] (Factor Store)
    ├─ 活动数据映射 (electricity → scope2)
    ├─ 因子选用 (中国电网2.024年因子)
    └─ 不确定性参数
    ↓
[碳排放计算] (Carbon Engine)
    ├─ 直接计算: emission = usage × factor
    ├─ 蒙特卡洛模拟: 10000次采样
    └─ 不确定性范围: ci95_low ~ ci95_high
    ↓
[风险检测] (Isolation Forest)
    ├─ 多维度特征: [electricity, logistics, return_rate, ...]
    ├─ 异常判断: predict() + score_samples()
    └─ 风险等级: low/medium/high
    ↓
[LLM报告生成] (Qwen-Plus @ DashScope)
    ├─ Prompt构建: 企业名/排放量/ESG/风控
    ├─ 创意生成: 600-1500字专业诊断报告
    └─ 降级Mock: 网络失败时自动生成
    ↓
用户获得：排放数据 + 风险评分 + 定制化报告
```

---

## 🔑 关键配置

### 环境变量 (.env)
```bash
DASHSCOPE_API_KEY=sk-xxx         # Qwen/VLM API Key
DASHSCOPE_MODELS=qwen-vl-max,qwen-vl-plus  # VLM模型列表
PYTHONENV=development           # 开发环境
```

### 数据库表清单
- `users` - 用户信息
- `analysis_results` - **核算结果(主表)**
- `analysis_breakdowns` - **排放分解**
- `analysis_result_v2_snapshot` - V2快照(新)
- `risk_results` - **风控结果**
- `raw_data_records` - 原始凭证
- `parsed_data_records` - 解析数据
- `activity_records` - 活动数据
- `carbon_records` - 碳排行为记录
- `emission_factors` - 排放因子
- `emission_factor_items` - 详细因子(新)

---

## ⚡ P0功能实装建议

### P0_1: Isolation Forest 异常检测强化
**现状**：基础Demo版本，使用随机生成的训练数据
**建议**：
1. 用真实企业数据重训练模型（真实的electricity_usage、carbon_intensity分布）
2. 添加特征工程：滚动Z-score、IQR检测、自适应阈值
3. 持久化：将训练好的model保存到 `models/risk_model.pkl`

### P0_2: LLM结构化报告
**现状**：支持Prompt→Text生成，但输出未结构化
**建议**：
1. 定义结构化输出Pydantic模型：
   ```python
   class StructuredReport:
       executive_summary: str
       emission_analysis: Dict  # {scope1/2/3}
       risk_assessment: Dict    # {risk_score, risk_level, recommendations}
       recommendations: List[str]  # [行动项1, 行动项2, ...]
   ```
2. 优化Prompt，要求JSON输出并加constraint parsing
3. 添加Markdown渲染（前端调用 `/api/reports/{id}/markdown`）

### P0_3: VLM票据兜底
**现状**：Confidence评分仅来自VLM自评
**建议**：
1. 多模型共识：Qwen-VLM-Max + Qwen-VL-Plus 投票
2. 人工审核队列：confidence < 0.6的自动入审核列表
3. 主动学习：用户修正的数据反馈到训练集
4. 集成OCR兜底：当VLM失败时，调用传统OCR (Tesseract/PaddleOCR)

---

## 📞 相关接口入口速查

| 功能 | 文件 | 类/函数 | 状态 |
|------|------|--------|------|
| 票据识别 | routers/ocr.py | `recognize()` | ✅实装 |
| 碳核算 | routers/carbon.py | `calculate()` | ⚠️未查到 |
| 风险检测 | routers/risk.py | `detect_risk()` | ✅实装 |
| 报告生成 | services/report_llm.py | `CarbonReportGenerator.generate()` | ✅实装 |
| 报告路由 | routers/reports.py | `generate_report()` | ⚠️数据库化 |
| VLM解析 | services/vlm_parser.py | `VLMParser.parse_document()` | ✅实装 |

---

## 🎯 快速检索

**我需要修改…报告生成逻辑** → [backend/services/report_llm.py](backend/services/report_llm.py)

**我需要看…Scope分解结果** → [backend/models/analysis_v2.py#L12](backend/models/analysis_v2.py#L12) (`scope_breakdown`)

**我需要集成…新的风险因子** → [backend/services/risk_detector.py#L22](backend/services/risk_detector.py#L22) (`RiskInputData`)

**我需要修改…前端交互流程** → [demo-flow.js#L1899](demo-flow.js#L1899) (`initDemoFlow()`)

**我需要了解…OCR失败降级机制** → [backend/services/vlm_parser.py#L74](backend/services/vlm_parser.py#L74) (`_parse_mock()`)

---

**更新时间**: 2025-04-16  
**分析人**: GitHub Copilot  
**覆盖范围**: 核心模块 + P0功能链路
