from .base import CarbonStrategy

class DefaultStrategy(CarbonStrategy):
    """普通企业默认核算"""
    def calculate(self, activity_data: dict, factor_store) -> dict:
        total = 0.0
        breakdown = []
        # 默认只算这 4 项
        activities = ["electricity", "natural_gas", "diesel", "waste"]
        
        for act in activities:
            amount = activity_data.get(act, 0.0)
            if amount > 0:
                factor_info = factor_store.get_factor(act, industry_type="general")
                emission = amount * factor_info["value"]
                total += emission
                breakdown.append({
                    "item": act,
                    "amount": amount,
                    "factor": factor_info["value"],
                    "emission": round(emission, 2),
                    "unit": factor_info.get("unit", ""),
                    "source": factor_info.get("source", ""),
                })
                
        return {"total_emission": round(total, 2), "breakdown": breakdown}


class CrossBorderStrategy(DefaultStrategy):
    """跨境店铺核算策略"""
    def calculate(self, activity_data: dict, factor_store) -> dict:
        # 先调用默认策略的基础核算
        result = super().calculate(activity_data, factor_store)
        total = result["total_emission"]
        breakdown = result["breakdown"]
        
        # 额外挂载: 航空物流 (air_logistics)、高耗能仓储 (warehouse_energy)
        extra_activities = ["air_logistics", "warehouse_energy"]
        for act in extra_activities:
            amount = activity_data.get(act, 0.0)
            if amount > 0:
                factor_info = factor_store.get_factor(act, industry_type="cross_border")
                emission = amount * factor_info["value"]
                total += emission
                breakdown.append({
                    "item": act,
                    "amount": amount,
                    "factor": factor_info["value"],
                    "emission": round(emission, 2),
                    "unit": factor_info.get("unit", ""),
                    "source": factor_info.get("source", ""),
                })
        
        return {"total_emission": round(total, 2), "breakdown": breakdown}


class DailyGoodsStrategy(DefaultStrategy):
    """日用百货核算策略"""
    def calculate(self, activity_data: dict, factor_store) -> dict:
        # 先调用默认策略的基础核算
        result = super().calculate(activity_data, factor_store)
        total = result["total_emission"]
        breakdown = result["breakdown"]
        
        # 额外挂载: 逆向物流 (reverse_logistics)、包装废弃物 (packaging_waste)
        extra_activities = ["reverse_logistics", "packaging_waste"]
        for act in extra_activities:
            amount = activity_data.get(act, 0.0)
            if amount > 0:
                factor_info = factor_store.get_factor(act, industry_type="daily_goods")
                emission = amount * factor_info["value"]
                total += emission
                breakdown.append({
                    "item": act,
                    "amount": amount,
                    "factor": factor_info["value"],
                    "emission": round(emission, 2),
                    "unit": factor_info.get("unit", ""),
                    "source": factor_info.get("source", ""),
                })
        
        return {"total_emission": round(total, 2), "breakdown": breakdown}
