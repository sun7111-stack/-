from typing import Dict, Any
from .strategies import DefaultStrategy, CrossBorderStrategy, DailyGoodsStrategy
from .factor_store import FactorStore

class CarbonEngine:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_strategy(self, shop_type: str):
        if shop_type == "cross_border":
            return CrossBorderStrategy()
        elif shop_type == "daily_goods":
            return DailyGoodsStrategy()
        return DefaultStrategy()
        
    def run_calculation(self, activity_data: dict, shop_type: str, region: str = "全国", revenue: float = 1000.0) -> dict:
        """
        入口函数：根据行业场景选择策略，传递活动数据和动态因子库，返回核算结果和分项明细。
        activity_data 示例: {"electricity": 1000, "air_logistics": 50}
        """
        strategy = self.get_strategy(shop_type)
        factor_store = FactorStore(self.db_session, region=region)
        
        # 1. 策略核算
        result = strategy.calculate(activity_data, factor_store)
        
        # 2. 挂载基准对比
        result["benchmark_compare"] = self.calculate_industry_deviation(result["total_emission"], shop_type, revenue)
        
        return result

    def calculate_industry_deviation(self, total_emission: float, shop_type: str, revenue: float = None) -> Dict[str, Any]:
        """计算行业对比及相对偏差 \Delta"""
        benchmarks = {
            "cross_border": 3100.0,
            "daily_goods": 2500.0,
            "general": 2800.0
        }
        e_avg = benchmarks.get(shop_type, 2800.0)
        
        # \Delta = (E_total - E_avg) / E_avg
        delta = (total_emission - e_avg) / e_avg if e_avg > 0 else 0.0
        pct_deviation = abs(delta) * 100
            
        if delta < -0.1:
            eval_label = "优秀"
            position_desc = f"低于行业平均 {pct_deviation:.1f}%"
        elif -0.1 <= delta < 0:
            eval_label = "良好"
            position_desc = f"略低于行业平均 {pct_deviation:.1f}%"
        elif 0 <= delta < 0.1:
            eval_label = "一般"
            position_desc = f"略高于行业平均 {pct_deviation:.1f}%"
        else:
            eval_label = "改进空间大"
            position_desc = f"高于行业平均 {pct_deviation:.1f}%"
            
        result = {
            "industry_avg": e_avg,
            "deviation_ratio": round(delta, 4),
            "position": position_desc,
            "rank_label": eval_label,
            "carbon_intensity": round(total_emission / revenue, 4) if revenue and revenue > 0 else 0.0
        }
        return result
