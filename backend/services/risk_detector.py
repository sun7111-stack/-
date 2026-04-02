"""Isolation Forest 风控检测服务"""
from pathlib import Path
from typing import List, Optional

import joblib
import numpy as np
from pydantic import BaseModel
from sklearn.ensemble import IsolationForest


class RiskInputData(BaseModel):
    electricity_usage: float
    logistics_distance: float
    return_rate: float
    total_emission: float
    carbon_intensity: float


class RiskOutputData(BaseModel):
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
