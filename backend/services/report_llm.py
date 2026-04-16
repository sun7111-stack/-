"""AIGC 报告生成服务（P0增强：结构化输入+受控输出）"""
import os
import json
import re
from typing import Dict, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

load_dotenv()


class ReportInputData(BaseModel):
    """P0增强：结构化报告输入"""
    company_name: str = "Demo企业"
    period: str = "本期"
    total_emission: float = 0.0
    carbon_intensity: float = 0.0
    industry_avg_intensity: float = 0.5
    emission_breakdown: List[Dict] = []
    
    # P0新增：风控相关
    risk_level: str = "low"  # low/medium/high
    risk_score: float = 0.0
    anomaly_reasons: List[str] = []  # Isolation Forest 返回的中文原因
    trust_score: float = 0.95  # 数据可信度(0-1)
    
    # P0新增：证据链信息
    evidence_confidence: float = 0.95  # 证据可信度
    evidence_chain_length: int = 0  # 证据链接数
    
    # P0新增：历史对比
    yoy_change: float = 0.0  # 同比增长率
    trend: str = "stable"  # stable/rising/falling
    
    # Legacy support
    esg_score: float = 75.0
    prompt: Optional[str] = None


class StructuredReportSection(BaseModel):
    """单个报告章节"""
    title: str
    content: str


class ReportOutputData(BaseModel):
    """P0增强：结构化报告输出（多章节）"""
    model_config = ConfigDict(protected_namespaces=())

    summary: str  # 执行摘要（50-100字）
    key_findings: List[str]  # 关键发现（3-5条）
    risk_explanation: str  # 风险原因与解释（100-200字）
    trust_statement: str  # 数据可信度说明（50-100字）
    optimization_suggestions: List[str]  # 优化建议（3-5条）
    
    # 元数据
    is_mock: bool
    model_used: str
    full_report: str  # 可选：完整文本拼接


class CarbonReportGenerator:
    """P0增强LLM报告生成器"""
    
    def __init__(self):
        self.dashscope = self._init_dashscope()
        self.mock_mode = self.dashscope is None

    def _init_dashscope(self):
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return None
        try:
            import dashscope
            dashscope.api_key = api_key
            return dashscope
        except ImportError:
            return None

    def _build_structured_prompt(self, body: ReportInputData) -> str:
        """P0新增：精心设计的结构化Prompt，引导Qwen生成JSON"""
        risk_section = ""
        if body.anomaly_reasons:
            risk_section = "风险原因：\n" + "\n".join(f"- {r}" for r in body.anomaly_reasons[:3])
        
        breakdown_lines = "\n".join(
            [f"- {item.get('source', '未知来源')}: {item.get('value', 0)} tCO2e ({item.get('proportion', 0)*100:.1f}%)"
             for item in body.emission_breakdown[:5]]
        )
        
        return f"""你是专业ESG与碳管理顾问。请根据以下企业碳数据，生成一份结构化诊断报告。

【企业信息】
企业名称：{body.company_name}
报告周期：{body.period}

【核算结果】
总排放量：{body.total_emission} tCO2e
碳强度：{body.carbon_intensity} tCO2e/万元
行业平均碳强度：{body.industry_avg_intensity} tCO2e/万元
排放贡献Top 5：
{breakdown_lines}

【风险评估】
风险等级：{body.risk_level}（低/中/高）
风险评分：{body.risk_score}/100
{risk_section}

【数据可信度】
数据可信度：{body.trust_score*100:.1f}%
证据链长度：{body.evidence_chain_length}个环节
证据可信度：{body.evidence_confidence*100:.1f}%

【环比对比】
同比变化：{body.yoy_change:+.1f}%
趋势判断：{'上升' if body.trend=='rising' else '下降' if body.trend=='falling' else '平稳'}

请生成JSON格式报告，包含以下5个字段：
1. summary：执行摘要（50-100字）
2. key_findings：3-5条关键发现（JSON数组）
3. risk_explanation：具体分析风险原因（100-200字）
4. trust_statement：数据质量与可信度说明（50-100字）
5. optimization_suggestions：3-5条可落地的优化建议（JSON数组）

必须返回有效的JSON对象，不含代码块标记。"""

    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """P0新增：从LLM响应中提取JSON"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except:
            pass
        
        # 尝试提取JSON块（```json...```）
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # 尝试查找最后一个JSON对象
        matches = list(re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text))
        if matches:
            for match in reversed(matches):
                try:
                    return json.loads(match.group(0))
                except:
                    continue
        
        return None

    def _mock_structured_report(self, body: ReportInputData) -> ReportOutputData:
        """P0增强：Mock报告生成（5章节结构）"""
        risk_text = "低风险" if body.risk_level == "low" else "中等风险" if body.risk_level == "medium" else "高风险"
        trend_text = "上升" if body.trend == "rising" else "下降" if body.trend == "falling" else "平稳"
        
        return ReportOutputData(
            summary=f"{body.company_name}在{body.period}总碳排放为{body.total_emission} tCO2e，碳强度{body.carbon_intensity} tCO2e/万元，整体风险评级{risk_text}。",
            key_findings=[
                f"碳排放总量与行业平均水平相比{'高于' if body.carbon_intensity > body.industry_avg_intensity else '低于'}行业平均{'约' + str(abs(round((body.carbon_intensity/body.industry_avg_intensity - 1)*100))) + '%' if body.industry_avg_intensity > 0 else ''}",
                f"主要排放来源为{body.emission_breakdown[0].get('source', '能源利用') if body.emission_breakdown else '能源利用'}，占比{body.emission_breakdown[0].get('proportion', 0)*100:.1f}%" if body.emission_breakdown else "排放结构分布均衡",
                f"同比{'增长' if body.yoy_change > 0 else '下降'}{abs(body.yoy_change):.1f}%，趋势{trend_text}",
                f"数据可信度{body.trust_score*100:.0f}%，建议持续完善数据治理流程",
            ],
            risk_explanation=f"当前企业风险等级为{risk_text}。主要风险因素包括：{'; '.join(body.anomaly_reasons[:2]) if body.anomaly_reasons else '暂无明显异常因素'}。建议重点监控关键排放源，建立月度复盘机制。",
            trust_statement=f"本报告基于{body.evidence_chain_length}个数据环节验证，可信度{body.trust_score*100:.0f}%。优化建议：进一步完善原始凭证收集、建立自动化数据采机制。",
            optimization_suggestions=[
                f"优化高排放源：识别Top 1排放来源，制定专项降低计划，目标降低10-20%",
                "推进清洁能源替代：评估光伏、风电、绿电采购等可再生能源方案",
                "建立碳数据管理体系：完善排放因子库、定期开展数据质量审计",
                "供应链协同减排：与上下游企业合作，推进范围3排放优化",
            ],
            is_mock=True,
            model_used="Mock Engine v2.0 (Structured)",
            full_report="",
        )

    def _call_qwen_structured(self, prompt: str) -> Optional[Dict]:
        """P0新增：调用Qwen生成结构化JSON输出"""
        if self.dashscope is None:
            return None
        try:
            resp = self.dashscope.Generation.call(
                model="qwen-plus",
                prompt=prompt,
                max_tokens=2000,
                temperature=0.5,  # 降低温度保证稳定性
                top_p=0.8,
            )
            if getattr(resp, "status_code", None) == 200:
                text = resp.output.text
                return self._parse_json_response(text)
        except Exception:
            pass
        return None

    def generate(self, body: ReportInputData) -> ReportOutputData:
        """P0完整流程：接收结构化输入，返回结构化输出"""
        prompt = self._build_structured_prompt(body)
        
        if self.mock_mode:
            return self._mock_structured_report(body)
        
        # 尝试调用Qwen获取结构化JSON
        json_data = self._call_qwen_structured(prompt)
        
        if json_data:
            # JSON解析成功，填充ReportOutputData
            try:
                return ReportOutputData(
                    summary=json_data.get("summary", "")[:120],
                    key_findings=json_data.get("key_findings", [])[:5],
                    risk_explanation=json_data.get("risk_explanation", "")[:250],
                    trust_statement=json_data.get("trust_statement", "")[:150],
                    optimization_suggestions=json_data.get("optimization_suggestions", [])[:5],
                    is_mock=False,
                    model_used="Qwen-Plus (Structured)",
                    full_report=json.dumps(json_data, ensure_ascii=False, indent=2),
                )
            except Exception:
                pass
        
        # 降级到Mock
        return self._mock_structured_report(body)


report_generator = CarbonReportGenerator()
