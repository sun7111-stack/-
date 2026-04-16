# 后端API路由对P0新增Service的适配分析

## 📍 三个关键路由位置

| 功能模块 | 文件位置 | 主要端点 | 状态 |
|---------|--------|--------|------|
| 风险检测 | `backend/routers/risk.py` | `POST /api/risk/detect` | ⚠️ 需要更新 |
| 报告生成 | `backend/routers/reports.py` | `POST /api/reports/generate-ai` | ⚠️ 需要更新 |
| OCR识别 | `backend/routers/ocr.py` | `POST /api/ocr/recognize` | ⚠️ 需要更新 |

---

## 1️⃣ 风险检测路由（[risk.py](backend/routers/risk.py)）

### 现在的实现
- **端点**: `POST /api/risk/detect`
- **请求模型**: `RiskDetectRequest`
  ```python
  class RiskDetectRequest(BaseModel):
      task_id: Optional[str] = None
      bill_id: Optional[str] = None
      raw_text: Optional[str] = ""
      structured_fields: Optional[dict] = None
      # 5个基础字段:
      electricity_usage: Optional[float] = None
      logistics_distance: Optional[float] = None
      return_rate: Optional[float] = None
      total_emission: Optional[float] = None
      carbon_intensity: Optional[float] = None
  ```

- **返回格式** (第170-196行):
  ```python
  {
      "success": True,
      "task_id": str,
      "is_anomaly": bool,
      "risk_score": float,
      "risk_score_explain": float,
      "risk_score_explain_v2": float,
      "risk_level": str,  # low/medium/high
      "trust_score": float,
      "trust_penalty": float,
      "risk_reasons": List[str],
      "risk_advice": List[str],
      "anomaly_labels": List[str],
      "details": List[str],
      "blockchain_hash": str,
      "trace_saved": bool,
      "model_version": str
  }
  ```

### Service新增内容（risk_detector.py）
- **RiskInputData** 新增6个字段:
  ```python
  energy_intensity: float = 0.5  # 能耗强度(kWh/万元)
  transport_emission_ratio: float = 0.0  # 物流排放占比(0-1)
  monthly_variation: float = 0.0  # 月度变异系数(0-1)
  warehouse_energy_ratio: float = 0.0  # 仓储能耗占比(0-1)
  scope3_share: float = 0.0  # Scope3占比(0-1)
  benchmark_deviation: float = 0.0  # 行业对标偏离度(0-1)
  ```

- **RiskOutputData** 新增3个关键字段:
  ```python
  anomaly_reasons: List[str]  # P0新增：中文解释
  optimization_advice: List[str]  # P0新增：优化建议
  feature_importance: Dict[str, float]  # P0新增：特征重要性
  ```

### 🔧 需要修改的地方

#### 修改1: 扩展RiskDetectRequest (第30-40行)
```python
# 现状: 只有5个基础字段
# 需要添加:
class RiskDetectRequest(BaseModel):
    # ... 现有字段 ...
    
    # P0新增特征（可选）
    energy_intensity: Optional[float] = None  # 能耗强度
    transport_emission_ratio: Optional[float] = None  # 物流排放占比
    monthly_variation: Optional[float] = None  # 月度变异系数
    warehouse_energy_ratio: Optional[float] = None  # 仓储能耗占比
    scope3_share: Optional[float] = None  # Scope3占比
    benchmark_deviation: Optional[float] = None  # 行业对标偏离度
```

#### 修改2: 更新_build_input_from_request函数 (第44-59行)
```python
def _build_input_from_request(body: RiskDetectRequest, latest: Optional[CarbonRecord]) -> RiskInputData:
    # ... 现有5个字段映射 ...
    
    # P0新增: 映射6个新字段（如果请求中没有则用默认值）
    return RiskInputData(
        electricity_usage=electricity_usage or 5000,
        logistics_distance=body.logistics_distance or 10000,
        return_rate=body.return_rate or 0.08,
        total_emission=total_emission or 50,
        carbon_intensity=carbon_intensity or 0.6,
        # P0新增映射:
        energy_intensity=body.energy_intensity or 0.5,
        transport_emission_ratio=body.transport_emission_ratio or 0.0,
        monthly_variation=body.monthly_variation or 0.0,
        warehouse_energy_ratio=body.warehouse_energy_ratio or 0.0,
        scope3_share=body.scope3_share or 0.0,
        benchmark_deviation=body.benchmark_deviation or 0.0,
    )
```

#### 修改3: 更新detect_risk返回值 (第170-196行)
```python
# 现状: 返回的数据来自旧版函数 (generate_risk_reasons, generate_risk_advice)
# 需要改用 RiskOutputData 中新增的字段:

risk_result = risk_detector.detect(detector_input)  # 已返回RiskOutputData

return {
    "success": True,
    "task_id": body.task_id or f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}",
    "is_anomaly": risk_result.is_anomaly,
    "risk_score": risk_result.risk_score,
    # ... 现有字段 ...
    
    # P0新增: 直接使用RiskOutputData的新字段
    "anomaly_reasons": risk_result.anomaly_reasons,  # 新增
    "optimization_advice": risk_result.optimization_advice,  # 新增
    "feature_importance": risk_result.feature_importance,  # 新增
}
```

#### 修改4: 更新DB存储 (第130-139行)
```python
# 现状: 只存储risk_reason/risk_advice字符串
# 改为: 也存储新的三个字段

db.add(
    RiskResult(
        user_id=current_user.id,
        analysis_id=latest_analysis.id if latest_analysis else None,
        risk_score=explain_score_v2,
        risk_level=risk_level,
        risk_reason="；".join(anomaly_reasons),  # 来自RiskOutputData
        risk_advice="；".join(optimization_advice),  # 来自RiskOutputData
        # P0新增（需要检查RiskResult模型是否有这些字段）:
        # anomaly_reasons_json: json.dumps(risk_result.anomaly_reasons),
        # feature_importance_json: json.dumps(risk_result.feature_importance),
    )
)
```

---

## 2️⃣ 报告生成路由（[reports.py](backend/routers/reports.py)）

### 现在的实现
- **端点**: `POST /api/reports/generate-ai`
- **请求处理** (第151-177行):
  ```python
  # 从request body解析: 直接使用dict接收
  report_input = ReportInputData(
      company_name=(current_user.company if current_user else "Demo企业"),
      period=body.get("period"),
      total_emission=float(body.get("total_emission") or 0.0),
      carbon_intensity=float(body.get("carbon_intensity") or 0.6),
      industry_avg_intensity=float(body.get("industry_avg_intensity") or 0.8),
      emission_breakdown=body.get("emission_breakdown") or [],
      risk_result=body.get("risk_result") or {...},  # 从风控返回结果获取
      esg_score=float(body.get("esg_score") or 75.0),
      prompt=body.get("prompt"),
  )
  ```

- **返回格式** (第177-194行):
  ```python
  {
      "success": True,
      "summary": str,  # 摘要
      "suggestions": List[str],
      "finance": str,  # 绿色金融建议
      "report_text": str  # 完整报告文本
  }
  ```

### Service新增内容（report_llm.py）
- **ReportInputData** 新增6个字段:
  ```python
  risk_level: str = "low"  # 风险级别
  risk_score: float = 0.0
  anomaly_reasons: List[str] = []  # Isolation Forest返回的原因
  trust_score: float = 0.95  # 数据可信度
  evidence_confidence: float = 0.95  # 证据可信度
  yoy_change: float = 0.0  # 同比增长率
  trend: str = "stable"  # stable/rising/falling
  ```

- **ReportOutputData** 新增5个结构化字段:
  ```python
  summary: str  # 执行摘要（50-100字）
  key_findings: List[str]  # 关键发现（3-5条）
  risk_explanation: str  # 风险原因与解释（100-200字）
  trust_statement: str  # 数据可信度说明（50-100字）
  optimization_suggestions: List[str]  # 优化建议（3-5条）
  ```

### 🔧 需要修改的地方

#### 修改1: 创建正式的ReportGenerate请求模型
```python
# 现状: 使用 dict 直接接收
# 新增: 使用强类型的Pydantic模型

from services.report_llm import ReportInputData

@router.post("/reports/generate-ai", summary="生成AIGC诊断报告")
def generate_ai_report(
    body: ReportInputData,  # 改用ReportInputData而不是dict
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
```

#### 修改2: 完整映射所有新字段 (第151-177行)
```python
# 现状: 只映射基础的8个字段
# 需要新增映射:

report_input = ReportInputData(
    company_name=...,
    period=...,
    total_emission=...,
    carbon_intensity=...,
    industry_avg_intensity=...,
    emission_breakdown=...,
    esg_score=...,
    prompt=...,
    
    # P0新增映射:
    risk_level=body.risk_level or "low",  # 新
    risk_score=body.risk_score or 0.0,  # 新
    anomaly_reasons=body.anomaly_reasons or [],  # 新（来自risk_detector）
    trust_score=body.trust_score or 0.95,  # 新（来自trust_score_record）
    evidence_confidence=body.evidence_confidence or 0.95,  # 新
    yoy_change=body.yoy_change or 0.0,  # 新
    trend=body.trend or "stable",  # 新
)
```

#### 修改3: 更新返回格式以匹配ReportOutputData (第177-194行)
```python
# 现状: 返回的是手工组装的字典
# 改为: 如果report_generator.generate返回ReportOutputData，则直接返回其内容

output = report_generator.generate(report_input)  # 返回ReportOutputData

return {
    "success": True,
    # 来自ReportOutputData:
    "summary": output.summary,  # 替代之前的第一行截断逻辑
    "key_findings": output.key_findings,  # P0新增
    "risk_explanation": output.risk_explanation,  # P0新增
    "trust_statement": output.trust_statement,  # P0新增
    "optimization_suggestions": output.optimization_suggestions,  # P0新增
    
    # 保留向后兼容:
    "suggestions": output.optimization_suggestions,  # 向后兼容
    "finance": "...",  # 保持不变或从trust_statement扩展
    "report_text": output.full_report,  # 保持不变
}
```

---

## 3️⃣ OCR识别路由（[ocr.py](backend/routers/ocr.py)）

### 现在的实现
- **端点**: `POST /api/ocr/recognize`
- **请求**: `file: UploadFile = File(...)`
- **返回模型**: `OCRResponse` (第60-73行)
  ```python
  class OCRParseResult(BaseModel):
      doc_type: str  # 票据类型
      confidence: float  # 置信度 0-1
      fields: Dict[str, Any]  # 结构化字段
      raw_text: str  # 原始文本
      suggested_activity_type: str  # 建议的碳核算活动类型
      raw_data: Optional[Dict[str, Any]] = None
      parsed_data: Optional[Dict[str, Any]] = None
      mapped_data: Optional[list] = None
      normalized_data: Optional[Dict[str, Any]] = None
      cleaned_record: Optional[Dict[str, Any]] = None
      chain_ids: Optional[Dict[str, Any]] = None
      message: Optional[str] = None
  ```

### Service新增内容（vlm_parser.py）
- **P0新增**: 复杂度检测函数 `_detect_document_complexity` (第74-99行)
  ```python
  # 返回: "simple" | "standard" | "complex"
  complexity = cls._detect_document_complexity(content, filename, mime_type)
  ```

- **P0新增**: parse_method字段  
  ```python
  "parse_method": "simple_heuristic"  # OCR简启发式
  "parse_method": "vlm_advanced(qwen-vl-max)"  # VLM高级模式
  "parse_method": "mock"  # Mock模式
  ```

- **P0新增**: complexity_notes字段 (在parse_vlm_advanced中)
  ```python
  6. complexity_notes: 在这份"{complexity}"文档中找到的特殊处理说明
  ```

### 🔧 需要修改的地方

#### 修改1: 扩展OCRParseResult模型 (第60-73行)
```python
class OCRParseResult(BaseModel):
    # ... 现有字段 ...
    
    # P0新增:
    parse_method: str = "unknown"  # "simple_heuristic" | "vlm_advanced(...)" | "mock"
    complexity: str = "standard"  # "simple" | "standard" | "complex"
    complexity_notes: Optional[str] = None  # 复杂度特殊说明
```

#### 修改2: 更新recognize端点返回 (第98-153行)
```python
# 现状: 调用parse_document_wrapper，返回原始result_data
# 需要: 确保返回中包含parse_method和complexity字段

result_data = await parse_document_wrapper(file)

# P0新增: 确保这些字段存在（vlm_parser已生成）
if "parse_method" not in result_data:
    result_data["parse_method"] = "unknown"
if "complexity" not in result_data:
    result_data["complexity"] = "standard"

return OCRResponse(
    success=True,
    data=OCRParseResult(**result_data),
    message="识别成功"
)
```

#### 修改3: 更新chain_check返回（同步复杂度信息）(第211-260行)
```python
# 可选: 在chain_check返回中添加parse_method和complexity信息
# 帮助前端展示文档处理方式

class OCRChainCheckResponse(BaseModel):
    success: bool
    raw_data: Optional[Dict[str, Any]] = None
    parsed_data: List[Dict[str, Any]] = []
    activity_data: List[Dict[str, Any]] = []
    
    # P0新增（可选）:
    parse_method: Optional[str] = None  # 解析方法
    complexity: Optional[str] = None  # 复杂度
    
    message: str = ""
```

---

## 📊 修改优先级与工作量预估

| 优先级 | 路由 | 修改项 | 工作量 | 优先理由 |
|------|------|--------|--------|--------|
| 🔴 P0   | risk.py | 扩展RiskDetectRequest (6字段) | 15分 | 风险检测是核心功能 |
| 🔴 P0   | risk.py | 更新返回格式(3个新字段) | 15分 | 前端需要的新信息 |
| 🟡 P1   | reports.py | 完整映射ReportInputData | 20分 | 报告质量依赖这些字段 |
| 🟡 P1   | reports.py | 结构化返回ReportOutputData | 20分 | 前端需要多章节内容 |
| 🟢 P2   | ocr.py | 添加parse_method/complexity | 10分 | 可观测性，非阻塞 |

**总工作量**: ~80分钟（包括测试）

---

## ✅ 检查清单

- [ ] risk.py: RiskDetectRequest增加6个新字段
- [ ] risk.py: _build_input_from_request映射新字段
- [ ] risk.py: detect_risk返回结果添加anomaly_reasons/optimization_advice/feature_importance
- [ ] reports.py: 修改generate_ai_report参数为ReportInputData
- [ ] reports.py: 完整映射所有新输入字段
- [ ] reports.py: 返回ReportOutputData的5个结构化字段
- [ ] ocr.py: OCRParseResult添加parse_method/complexity/complexity_notes
- [ ] ocr.py: recognize端点确保这些字段正确传递
- [ ] 数据模型: 检查RiskResult表是否需要新的JSON字段来存储feature_importance
- [ ] 回归测试: 三个端点的完整流程测试

---

## 🔗 相关文件导航

- Service新增: [risk_detector.py](backend/services/risk_detector.py) / [report_llm.py](backend/services/report_llm.py) / [vlm_parser.py](backend/services/vlm_parser.py)
- 现有路由: [risk.py](backend/routers/risk.py) / [reports.py](backend/routers/reports.py) / [ocr.py](backend/routers/ocr.py)
- 数据模型: [models/](backend/models/) 目录
- Schemas: [schemas/](backend/schemas/) 目录

