"""AIGC 报告生成服务（有 Key 走模型，无 Key 自动 Mock）"""
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

load_dotenv()


class ReportInputData(BaseModel):
    company_name: str = "Demo企业"
    period: str = "本期"
    total_emission: float = 0.0
    carbon_intensity: float = 0.0
    industry_avg_intensity: float = 0.5
    emission_breakdown: List[Dict] = []
    risk_result: Dict = {}
    esg_score: float = 75.0
    prompt: Optional[str] = None


class ReportOutputData(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    report_text: str
    is_mock: bool
    model_used: str


class CarbonReportGenerator:
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

    def _build_prompt(self, body: ReportInputData) -> str:
        if body.prompt:
            return (
                "你是企业碳管理顾问，请用专业中文给出诊断建议。\n"
                f"用户问题：{body.prompt}\n"
                f"总排放：{body.total_emission} tCO2e\n"
                f"碳强度：{body.carbon_intensity} tCO2e/万元\n"
                f"ESG分数：{body.esg_score}\n"
                f"风控结果：{body.risk_result}"
            )

        breakdown_lines = "\n".join(
            [f"- {item.get('source', '未知来源')}: {item.get('value', 0)} tCO2e" for item in body.emission_breakdown]
        )
        return (
            "请基于以下企业量化指标生成一份专业碳诊断报告，控制在600字左右。\n"
            f"企业：{body.company_name}\n"
            f"周期：{body.period}\n"
            f"总排放：{body.total_emission} tCO2e\n"
            f"碳强度：{body.carbon_intensity} tCO2e/万元\n"
            f"行业平均碳强度：{body.industry_avg_intensity} tCO2e/万元\n"
            f"ESG分数：{body.esg_score}\n"
            f"风控结果：{body.risk_result}\n"
            f"分项排放：\n{breakdown_lines}\n"
            "请输出：总体结论、风险提示、三条可落地建议。"
        )

    def _mock_report(self, body: ReportInputData) -> str:
        return (
            f"{body.company_name}在{body.period}总碳排放为{body.total_emission} tCO2e，"
            f"碳强度为{body.carbon_intensity} tCO2e/万元，ESG得分{body.esg_score}。"
            "建议优先优化高耗能环节、推动绿色电力替代、建立月度碳数据复盘机制。"
        )

    def _call_qwen(self, prompt: str) -> Optional[str]:
        if self.dashscope is None:
            return None
        try:
            resp = self.dashscope.Generation.call(
                model="qwen-plus",
                prompt=prompt,
                max_tokens=1500,
                temperature=0.6,
                top_p=0.8,
            )
            if getattr(resp, "status_code", None) == 200:
                return resp.output.text
        except Exception:
            return None
        return None

    def generate(self, body: ReportInputData) -> ReportOutputData:
        prompt = self._build_prompt(body)

        if self.mock_mode:
            return ReportOutputData(
                report_text=self._mock_report(body),
                is_mock=True,
                model_used="Mock Engine v1.0",
            )

        text = self._call_qwen(prompt)
        if not text:
            return ReportOutputData(
                report_text=self._mock_report(body),
                is_mock=True,
                model_used="Mock Engine v1.0 (Fallback)",
            )

        return ReportOutputData(report_text=text, is_mock=False, model_used="Qwen")


report_generator = CarbonReportGenerator()
