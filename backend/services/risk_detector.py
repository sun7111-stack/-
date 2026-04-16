"""Isolation Forest 风控检测服务"""
from pathlib import Path
from typing import List, Optional, Dict, Any

import joblib
import numpy as np
from pydantic import BaseModel, ConfigDict
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class RiskInputData(BaseModel):
    """6维异常检测特征"""
    electricity_usage: float  # 用电量(kWh)
    logistics_distance: float  # 物流距离(km)
    return_rate: float  # 退货率(0-1)
    total_emission: float  # 总排放(tCO2e)
    carbon_intensity: float  # 碳强度(tCO2e/万元)
    # P0新增：前沿特征
    energy_intensity: float = 0.5  # 能耗强度(kWh/万元) - 单位能耗
    transport_emission_ratio: float = 0.0  # 物流排放占比(0-1) - 运输等排/总排
    monthly_variation: float = 0.0  # 月度变异系数(0-1) - 短期波动度
    warehouse_energy_ratio: float = 0.0  # 仓储能耗占比(0-1) - 冷链仓储等
    scope3_share: float = 0.0  # Scope3占比(0-1) - 间接排放比重
    benchmark_deviation: float = 0.0  # 行业对标偏离度(0-1) - 与同行对比


class RiskOutputData(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    is_anomaly: bool
    risk_score: float  # 0-100
    anomaly_labels: List[str]  # 细粒度风险标签
    anomaly_reasons: List[str]  # P0新增：中文解释
    optimization_advice: List[str]  # P0新增：优化建议
    feature_importance: Dict[str, float]  # P0新增：特征重要性
    model_version: str = "2.0.0-P0"


class IsolationForestRiskDetector:
    """P0增强版：增加6维特征工程、异常原因解释、优化建议"""
    
    def __init__(self, model_path: str = "./models/risk_model_v2.pkl"):
        self.model_path = Path(model_path)
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.score_threshold = 60.0
        self.feature_names = [
            "electricity_usage",
            "logistics_distance", 
            "return_rate",
            "total_emission",
            "carbon_intensity",
            "energy_intensity",
            "transport_emission_ratio",
            "monthly_variation",
            "warehouse_energy_ratio",
            "scope3_share",
            "benchmark_deviation",
        ]
        self._init_model()

    def _init_model(self):
        if self.model_path.exists():
            try:
                data = joblib.load(self.model_path)
                self.model = data.get("model")
                self.scaler = data.get("scaler")
                return
            except:
                pass
        self._train_demo_model()

    def _train_demo_model(self):
        """训练带6维特征的 Isolation Forest 模型"""
        np.random.seed(42)
        n_samples = 1000
        
        # 生成11维特征的正常样本：混合正态分布与Beta分布模拟真实业务数据
        normal_data = np.column_stack([
            np.random.normal(loc=5000, scale=2000, size=n_samples),      # electricity_usage
            np.random.normal(loc=10000, scale=5000, size=n_samples),     # logistics_distance
            np.random.beta(a=2, b=20, size=n_samples),                   # return_rate
            np.random.normal(loc=50, scale=20, size=n_samples),          # total_emission
            np.random.normal(loc=0.5, scale=0.2, size=n_samples),        # carbon_intensity
            np.random.normal(loc=0.8, scale=0.3, size=n_samples),        # energy_intensity (新)
            np.random.beta(a=3, b=7, size=n_samples),                    # transport_emission_ratio (新)
            np.random.gamma(shape=2, scale=0.1, size=n_samples),         # monthly_variation (新)
            np.random.beta(a=2, b=5, size=n_samples),                    # warehouse_energy_ratio (新)
            np.random.beta(a=2, b=8, size=n_samples),                    # scope3_share (新)
            np.random.normal(loc=0.1, scale=0.15, size=n_samples),       # benchmark_deviation (新)
        ])
        
        # 标准化特征
        self.scaler = StandardScaler()
        normal_data_scaled = self.scaler.fit_transform(normal_data)
        
        # 训练 Isolation Forest
        self.model = IsolationForest(
            n_estimators=150,  # 提高估计器数量
            max_samples="auto",
            contamination=0.08,  # 调整污染率
            random_state=42,
        )
        self.model.fit(normal_data_scaled)
        
        # 保存模型与标准化器
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "scaler": self.scaler}, self.model_path)

    def _calculate_risk_score(self, anomaly_score: float) -> float:
        """将异常分转换为0-100风险分"""
        normalized_score = (1 - anomaly_score) / 2
        return round(float(max(0, min(100, normalized_score * 100))), 2)

    def _extract_features(self, input_data: RiskInputData) -> np.ndarray:
        """提取并标准化11维特征"""
        features = np.array([[
            input_data.electricity_usage,
            input_data.logistics_distance,
            input_data.return_rate,
            input_data.total_emission,
            input_data.carbon_intensity,
            input_data.energy_intensity,
            input_data.transport_emission_ratio,
            input_data.monthly_variation,
            input_data.warehouse_energy_ratio,
            input_data.scope3_share,
            input_data.benchmark_deviation,
        ]])
        
        if self.scaler:
            features = self.scaler.transform(features)
        return features

    def _get_anomaly_labels(self, input_data: RiskInputData) -> List[str]:
        """规则型异常检测标签（保持向后兼容）"""
        labels = []
        if input_data.electricity_usage > 15000:
            labels.append("用电量异常偏高")
        if input_data.logistics_distance > 30000:
            labels.append("物流距离异常偏长")
        if input_data.return_rate > 0.3:
            labels.append("退货率异常偏高")
        if input_data.carbon_intensity > 1.5:
            labels.append("碳强度显著高于行业水平")
        return labels or ["综合数据模式异常"]

    def _get_anomaly_reasons(self, input_data: RiskInputData, anomaly_score: float) -> List[str]:
        """P0新增：基于6维特征的中文解释"""
        reasons = []
        
        # 能耗强度异常
        if input_data.energy_intensity > 1.2:
            reasons.append("单位能耗异常：能耗强度超出行业标准范围，建议检查设备效率")
        
        # 物流排放占比异常
        if input_data.transport_emission_ratio > 0.5:
            reasons.append("物流排放失衡：范围3排放占比过高，可能存在供应链冗余")
        
        # 短期波动异常（突变异常）
        if input_data.monthly_variation > 0.4:
            reasons.append("排放波动剧烈：月度数据差异大，可能存在异常业务高峰或数据质量问题")
        
        # 冷链仓储能耗异常
        if input_data.warehouse_energy_ratio > 0.35:
            reasons.append("仓储能耗占比高：冷链或仓库运营成本偏高，是重点优化区域")
        
        # Scope3占比异常（间接排放过高）
        if input_data.scope3_share > 0.65:
            reasons.append("间接排放占比高：供应链与物流排放是主要贡献者，需链条优化")
        
        # 行业对标偏离
        if input_data.benchmark_deviation > 0.3:
            reasons.append("对标偏离显著：碳强度与同行业差距较大，应分析行业竞争力")
        
        return reasons or ["综合指标在合理范围内，无显著异常"]

    def _get_optimization_advice(self, input_data: RiskInputData, reasons: List[str]) -> List[str]:
        """P0新增：针对性优化建议"""
        advice = []
        
        if input_data.energy_intensity > 1.2:
            advice.append("✓ 能效优化：进行设备能耗审计，优先更新低效电机、空调等高耗能设备")
        
        if input_data.transport_emission_ratio > 0.5:
            advice.append("✓ 物流优化：推进就近采购、多式联运，减少长距离运输")
        
        if input_data.monthly_variation > 0.4:
            advice.append("✓ 需求管理：建立合理库存策略，平滑生产波动，降低异常成本")
        
        if input_data.warehouse_energy_ratio > 0.35:
            advice.append("✓ 仓储改造：升级冷链控温技术、推进自然冷却、优化仓储布局")
        
        if input_data.scope3_share > 0.65:
            advice.append("✓ 链条协同：与供应商开展减排合作，推进绿色物流联盟")
        
        if input_data.carbon_intensity > 1.5:
            advice.append("✓ 清洁能源：加大光伏、风电等可再生能源比例，推进绿电采购协议")
        
        return advice or ["✓ 继续保持现有路线，定期监控关键指标变化"]

    def _calculate_feature_importance(self, input_data: RiskInputData) -> Dict[str, float]:
        """P0新增：计算特征对异常分的贡献度（基于偏离度）"""
        features = {
            "electricity_usage": min(input_data.electricity_usage / 15000, 1.0),
            "logistics_distance": min(input_data.logistics_distance / 30000, 1.0),
            "return_rate": min(input_data.return_rate / 0.3, 1.0),
            "carbon_intensity": min(input_data.carbon_intensity / 1.5, 1.0),
            "energy_intensity": min(input_data.energy_intensity / 1.2, 1.0),
            "transport_emission_ratio": input_data.transport_emission_ratio,
            "monthly_variation": min(input_data.monthly_variation / 0.4, 1.0),
            "warehouse_energy_ratio": min(input_data.warehouse_energy_ratio / 0.35, 1.0),
            "scope3_share": input_data.scope3_share,
            "benchmark_deviation": min(input_data.benchmark_deviation / 0.3, 1.0),
        }
        
        # 规范化到0-100
        max_val = max(features.values()) if features.values() else 1.0
        return {k: round(v / max_val * 100, 2) for k, v in features.items()}

    def detect(self, input_data: RiskInputData) -> RiskOutputData:
        """P0完整异常检测流程"""
        features = self._extract_features(input_data)
        
        anomaly_label = self.model.predict(features)[0]
        anomaly_score = self.model.score_samples(features)[0]
        risk_score = self._calculate_risk_score(anomaly_score)
        
        is_anomaly = (anomaly_label == -1) or (risk_score > self.score_threshold)
        anomaly_labels = self._get_anomaly_labels(input_data)
        anomaly_reasons = self._get_anomaly_reasons(input_data, anomaly_score)
        optimization_advice = self._get_optimization_advice(input_data, anomaly_reasons)
        feature_importance = self._calculate_feature_importance(input_data)
        
        return RiskOutputData(
            is_anomaly=is_anomaly,
            risk_score=risk_score,
            anomaly_labels=anomaly_labels,
            anomaly_reasons=anomaly_reasons,  # P0新增
            optimization_advice=optimization_advice,  # P0新增
            feature_importance=feature_importance,  # P0新增
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
