"""Isolation Forest 风控检测服务"""
from pathlib import Path
from typing import List, Optional

import joblib
import numpy as np
from pydantic import BaseModel, ConfigDict
from sklearn.ensemble import IsolationForest


class RiskInputData(BaseModel):
    electricity_usage: float
    logistics_distance: float
    return_rate: float
    total_emission: float
    carbon_intensity: float


class RiskOutputData(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    is_anomaly: bool
    risk_score: float
    anomaly_labels: List[str]
    model_version: str = "1.0.0"


class IsolationForestRiskDetector:
    def __init__(self, model_path: str = "./models/risk_model.pkl"):
        self.model_path = Path(model_path)
        self.model: Optional[IsolationForest] = None
        self.score_threshold = 60.0
        self._init_model()

    def _init_model(self):
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)
            return
        self._train_demo_model()

    def _train_demo_model(self):
        np.random.seed(42)
        n_samples = 1000
        normal_data = np.array(
            [
                np.random.normal(loc=5000, scale=2000, size=n_samples),
                np.random.normal(loc=10000, scale=5000, size=n_samples),
                np.random.beta(a=2, b=20, size=n_samples),
                np.random.normal(loc=50, scale=20, size=n_samples),
                np.random.normal(loc=0.5, scale=0.2, size=n_samples),
            ]
        ).T

        self.model = IsolationForest(
            n_estimators=100,
            max_samples="auto",
            contamination=0.1,
            random_state=42,
        )
        self.model.fit(normal_data)

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, self.model_path)

    def _calculate_risk_score(self, anomaly_score: float) -> float:
        normalized_score = (1 - anomaly_score) / 2
        return round(float(normalized_score * 100), 2)

    def _get_anomaly_labels(self, input_data: RiskInputData) -> List[str]:
        labels = []
        if input_data.electricity_usage > 15000:
            labels.append("用电量异常偏高")
        if input_data.logistics_distance > 30000:
            labels.append("物流距离异常偏长")
        if input_data.return_rate > 0.3:
            labels.append("退货率异常偏高")
        if input_data.carbon_intensity > 1.5:
            labels.append("碳强度显著高于行业水平")
        if not labels:
            labels.append("综合数据模式异常")
        return labels

    def detect(self, input_data: RiskInputData) -> RiskOutputData:
        features = np.array(
            [[
                input_data.electricity_usage,
                input_data.logistics_distance,
                input_data.return_rate,
                input_data.total_emission,
                input_data.carbon_intensity,
            ]]
        )

        anomaly_label = self.model.predict(features)[0]
        anomaly_score = self.model.score_samples(features)[0]
        risk_score = self._calculate_risk_score(anomaly_score)

        return RiskOutputData(
            is_anomaly=(anomaly_label == -1) or (risk_score > self.score_threshold),
            risk_score=risk_score,
            anomaly_labels=self._get_anomaly_labels(input_data),
        )


risk_detector = IsolationForestRiskDetector()


def calculate_risk_score(
    carbon_risk: float,
    esg_risk: float,
    governance_risk: float,
    w1: float = 0.5,
    w2: float = 0.3,
    w3: float = 0.2,
) -> float:
    """规则型组合风险分: R = w1*Rc + w2*Re + w3*Rg"""
    score = w1 * carbon_risk + w2 * esg_risk + w3 * governance_risk
    return round(max(0.0, min(100.0, score)), 2)


def calculate_risk_score_v2(
    carbon_risk: float,
    esg_risk: float,
    governance_risk: float,
    trust_score: float,
    anomaly_risk: float,
    l1: float = 0.30,
    l2: float = 0.20,
    l3: float = 0.15,
    l4: float = 0.20,
    l5: float = 0.15,
) -> float:
    """融合可信度与异常项的综合风险分。

    R = l1*Rc + l2*Resg + l3*Rg + l4*(1-T)*100 + l5*Ranomaly
    trust_score 取值区间 [0, 1]。
    """
    t = max(0.0, min(1.0, trust_score))
    trust_penalty = (1.0 - t) * 100.0
    score = (
        l1 * carbon_risk
        + l2 * esg_risk
        + l3 * governance_risk
        + l4 * trust_penalty
        + l5 * anomaly_risk
    )
    return round(max(0.0, min(100.0, score)), 2)


def classify_risk_level(risk_score: float) -> str:
    if risk_score >= 80:
        return "high"
    if risk_score >= 60:
        return "medium"
    return "low"


def generate_risk_reasons(
    carbon_risk: float,
    esg_risk: float,
    governance_risk: float,
    anomaly_labels: List[str],
) -> List[str]:
    reasons: List[str] = []
    if carbon_risk >= 70:
        reasons.append("碳排风险偏高：总排放或碳强度超出安全区间")
    if esg_risk >= 60:
        reasons.append("ESG风险偏高：环境或治理指标存在短板")
    if governance_risk >= 60:
        reasons.append("治理/信用风险偏高：退货率或运营稳定性需关注")
    for label in anomaly_labels:
        if label not in reasons:
            reasons.append(label)
    return reasons or ["未发现显著风险原因"]


def generate_risk_advice(risk_level: str, reasons: List[str]) -> List[str]:
    advice: List[str] = []
    if risk_level == "high":
        advice.append("立即启动专项整改，优先治理高耗能与高波动业务环节")
        advice.append("建立周度风控复盘和阈值预警机制")
    elif risk_level == "medium":
        advice.append("按月跟踪碳强度与退货率，优化异常环节")
        advice.append("补齐ESG披露与内控流程，降低治理不确定性")
    else:
        advice.append("保持现有管理策略，持续监控关键风险指标")

    if any("碳排" in r or "碳强度" in r for r in reasons):
        advice.append("推进节能改造与绿色电力替代，降低碳排放暴露")
    if any("治理" in r or "信用" in r for r in reasons):
        advice.append("完善内控与审计流程，提升治理透明度")

    return advice
