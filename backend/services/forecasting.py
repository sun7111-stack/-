"""时序预测服务：滑窗特征 + XGBoost(可选) + Conformal 区间。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np

try:
    from xgboost import XGBRegressor  # type: ignore

    XGBOOST_AVAILABLE = True
except Exception:
    XGBOOST_AVAILABLE = False

from sklearn.ensemble import RandomForestRegressor


@dataclass
class ForecastPoint:
    month: str
    value: float
    lower: float
    upper: float
    is_high_risk: bool


class CarbonForecastService:
    """轻量预测器，默认使用滑窗监督学习。"""

    def __init__(self, window_size: int = 3):
        self.window_size = max(2, window_size)

    def _build_supervised(self, series: List[float]) -> Tuple[np.ndarray, np.ndarray]:
        x_rows: List[List[float]] = []
        y_rows: List[float] = []
        for i in range(self.window_size, len(series)):
            x_rows.append(series[i - self.window_size : i])
            y_rows.append(series[i])
        if not x_rows:
            return np.empty((0, self.window_size)), np.empty((0,))
        return np.array(x_rows, dtype=float), np.array(y_rows, dtype=float)

    def _pick_model(self):
        if XGBOOST_AVAILABLE:
            return (
                XGBRegressor(
                    n_estimators=200,
                    max_depth=4,
                    learning_rate=0.05,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    random_state=42,
                    objective="reg:squarederror",
                ),
                "XGBoost(sliding-window)",
            )
        return (
            RandomForestRegressor(n_estimators=300, random_state=42),
            "RandomForest(sliding-window,fallback)",
        )

    def _future_months(self, last_month: str, steps: int) -> List[str]:
        base = datetime.strptime(last_month + "-01", "%Y-%m-%d")
        months = []
        y, m = base.year, base.month
        for _ in range(steps):
            m += 1
            if m > 12:
                m = 1
                y += 1
            months.append(f"{y:04d}-{m:02d}")
        return months

    def forecast(
        self,
        monthly_series: Dict[str, float],
        months_ahead: int = 6,
        alpha: float = 0.1,
    ) -> Dict:
        """返回预测值、Conformal 区间、动态阈值和高风险月份。"""
        if not monthly_series:
            return {
                "model_used": "n/a",
                "window_size": self.window_size,
                "history": [],
                "forecast": [],
                "dynamic_threshold": 0.0,
                "high_risk_months": [],
                "notes": ["缺少历史数据，无法预测"],
            }

        month_keys = sorted(monthly_series.keys())
        y_hist = [float(monthly_series[m]) for m in month_keys]

        if len(y_hist) < self.window_size + 2:
            avg = float(np.mean(y_hist))
            future = self._future_months(month_keys[-1], months_ahead)
            fallback = []
            for fm in future:
                fallback.append(
                    {
                        "month": fm,
                        "value": round(avg, 4),
                        "lower": round(max(0.0, avg * 0.85), 4),
                        "upper": round(avg * 1.15, 4),
                        "is_high_risk": False,
                    }
                )
            return {
                "model_used": "MeanBaseline(fallback)",
                "window_size": self.window_size,
                "history": [{"month": m, "value": monthly_series[m]} for m in month_keys],
                "forecast": fallback,
                "dynamic_threshold": round(avg * 1.2, 4),
                "high_risk_months": [],
                "notes": ["历史样本偏少，使用均值基线预测"],
            }

        x, y = self._build_supervised(y_hist)
        model, model_name = self._pick_model()

        calib_n = max(1, int(len(y) * 0.2))
        train_x, train_y = x[:-calib_n], y[:-calib_n]
        calib_x, calib_y = x[-calib_n:], y[-calib_n:]

        if len(train_y) == 0:
            train_x, train_y = x, y
            calib_x, calib_y = x, y

        model.fit(train_x, train_y)

        calib_pred = model.predict(calib_x)
        residuals = np.abs(calib_y - calib_pred)
        q = float(np.quantile(residuals, 1 - alpha)) if len(residuals) else 0.0

        rolling = y_hist[-self.window_size :]
        future_months = self._future_months(month_keys[-1], months_ahead)
        points: List[ForecastPoint] = []

        for idx in range(months_ahead):
            feat = np.array(rolling[-self.window_size :], dtype=float).reshape(1, -1)
            pred = float(model.predict(feat)[0])
            pred = max(0.0, pred)
            lower = max(0.0, pred - q)
            upper = pred + q
            points.append(
                ForecastPoint(
                    month=future_months[idx],
                    value=pred,
                    lower=lower,
                    upper=upper,
                    is_high_risk=False,
                )
            )
            rolling.append(pred)

        hist_mean = float(np.mean(y_hist))
        hist_std = float(np.std(y_hist))
        dynamic_threshold = hist_mean + 1.5 * hist_std

        high_risk = []
        for p in points:
            p.is_high_risk = p.upper >= dynamic_threshold
            if p.is_high_risk:
                high_risk.append(
                    {
                        "month": p.month,
                        "upper": round(p.upper, 4),
                        "threshold": round(dynamic_threshold, 4),
                        "reason": "预测上界超过动态预警阈值",
                    }
                )

        return {
            "model_used": model_name,
            "window_size": self.window_size,
            "conformal_alpha": alpha,
            "history": [{"month": m, "value": monthly_series[m]} for m in month_keys],
            "forecast": [
                {
                    "month": p.month,
                    "value": round(p.value, 4),
                    "lower": round(p.lower, 4),
                    "upper": round(p.upper, 4),
                    "is_high_risk": p.is_high_risk,
                }
                for p in points
            ],
            "dynamic_threshold": round(dynamic_threshold, 4),
            "high_risk_months": high_risk,
            "notes": [
                "区间由 Split-Conformal 残差分位数生成",
                "适合答辩展示：趋势预测 + 不确定性 + 风险预警",
            ],
        }


forecast_service = CarbonForecastService(window_size=3)
