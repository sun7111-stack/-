from typing import Dict, Any, List, Optional, Tuple

from .strategies import DefaultStrategy, CrossBorderStrategy, DailyGoodsStrategy
from .factor_store import FactorStore


class CarbonEngine:
    def __init__(self, db_session):
        self.db_session = db_session
        self.scope_mapping = {
            "electricity": ("S2", None, "production"),
            "natural_gas": ("S1", None, "production"),
            "diesel": ("S1", None, "transport"),
            "waste": ("S3", "waste", "storage"),
            "air_logistics": ("S3", "upstream_transport", "transport"),
            "reverse_logistics": ("S3", "reverse_logistics", "transport"),
            "warehouse_energy": ("S3", "upstream_operation", "storage"),
            "packaging_waste": ("S3", "packaging", "procurement"),
        }
        self.dqi_to_uncertainty = {
            "A": 0.03,
            "B": 0.06,
            "C": 0.10,
            "D": 0.20,
        }

    def get_strategy(self, shop_type: str):
        if shop_type == "cross_border":
            return CrossBorderStrategy()
        elif shop_type == "daily_goods":
            return DailyGoodsStrategy()
        return DefaultStrategy()

    def run_calculation(
        self,
        records: Optional[List[dict]] = None,
        enterprise_profile: Optional[dict] = None,
        model_version: str = "v2",
        uncertainty_mode: str = "analytic",
        activity_data: Optional[dict] = None,
        shop_type: str = "general",
        region: str = "全国",
        revenue: float = 1000.0,
    ) -> dict:
        """
        入口函数：支持 v1/v2 分流。
        """
        profile = enterprise_profile or {
            "shop_type": shop_type,
            "region": region,
            "annual_revenue": revenue,
            "year": None,
            "method": "default",
        }

        if records is None:
            records = []
            for k, v in (activity_data or {}).items():
                if (v or 0) > 0:
                    records.append(
                        {
                            "activity_id": None,
                            "activity_type": k,
                            "amount": float(v),
                            "unit": "",
                            "region": profile.get("region", "全国"),
                            "period": "",
                            "method": profile.get("method", "default"),
                            "dq_activity_level": "C",
                        }
                    )

        if model_version == "v1":
            return self.run_v1(records=records, enterprise_profile=profile)
        return self.run_v2(records=records, enterprise_profile=profile, uncertainty_mode=uncertainty_mode)

    def run_v1(self, records: List[dict], enterprise_profile: dict) -> dict:
        """兼容旧逻辑：仅返回总量+分项+基准+碳流。"""
        shop_type = enterprise_profile.get("shop_type", "general")
        region = enterprise_profile.get("region", "全国")
        revenue = float(enterprise_profile.get("annual_revenue", 1000.0) or 1000.0)

        activity_data = {r.get("activity_type", ""): float(r.get("amount", 0.0) or 0.0) for r in records}
        strategy = self.get_strategy(shop_type)
        factor_store = FactorStore(self.db_session, region=region)
        result = strategy.calculate(activity_data, factor_store)
        result["benchmark_compare"] = self.calculate_industry_deviation(result["total_emission"], shop_type, revenue)
        result["carbon_flow"] = self.build_carbon_flow(result.get("breakdown", []))
        result["model_version"] = "v1"
        return result

    def run_v2(self, records: List[dict], enterprise_profile: dict, uncertainty_mode: str = "analytic") -> dict:
        shop_type = enterprise_profile.get("shop_type", "general")
        region = enterprise_profile.get("region", "全国")
        revenue = float(enterprise_profile.get("annual_revenue", 1000.0) or 1000.0)
        year = enterprise_profile.get("year")
        method = enterprise_profile.get("method", "default")

        items: List[dict] = []
        for rec in records:
            scope, scope3_category = self.classify_scope(rec)
            factor_match = self.match_emission_factor(
                activity_type=rec.get("activity_type", ""),
                region=rec.get("region") or region,
                year=year,
                method=rec.get("method") or method,
                industry_type=shop_type,
            )
            emission_item = self.calculate_emission(rec, factor_match)
            emission_item["scope"] = scope
            emission_item["scope3_category"] = scope3_category
            emission_item["stage"] = self.scope_mapping.get(rec.get("activity_type", ""), ("S3", None, "production"))[2]
            items.append(emission_item)

        aggregated = self.aggregate_emission(items)
        uncertainty = self.propagate_uncertainty(items, mode=uncertainty_mode)
        top_contributors = sorted(items, key=lambda x: x.get("emission", 0.0), reverse=True)[:5]
        carbon_flow_graph = self.build_carbon_flow_graph(aggregated.get("source_breakdown", []), self.scope_mapping)

        benchmark_compare = self.calculate_industry_deviation(
            total_emission=aggregated.get("total_emission", 0.0),
            shop_type=shop_type,
            revenue=revenue,
        )

        explain_trace = self.build_explain_trace(
            analysis_id=None,
            items=items,
            benchmark_compare=benchmark_compare,
            uncertainty=uncertainty,
        )

        return {
            "model_version": "v2",
            "total_emission": aggregated.get("total_emission", 0.0),
            "breakdown": aggregated.get("source_breakdown", []),
            "scope_breakdown": aggregated.get("scope_breakdown", {}),
            "benchmark_compare": benchmark_compare,
            "uncertainty": uncertainty,
            "top_contributors": top_contributors,
            "factor_trace": [
                {
                    "activity_id": i.get("activity_id"),
                    "activity_type": i.get("activity_type"),
                    "matched_factor": i.get("factor_meta", {}),
                    "match_reason": i.get("factor_meta", {}).get("match_reason", ""),
                }
                for i in items
            ],
            "carbon_flow": carbon_flow_graph,
            "explain_trace": explain_trace,
        }

    def classify_scope(self, activity_record: dict) -> Tuple[str, Optional[str]]:
        activity_type = activity_record.get("activity_type", "")
        scope, category, _ = self.scope_mapping.get(activity_type, ("S3", "other", "production"))
        return scope, category

    def match_emission_factor(
        self,
        activity_type: str,
        region: str,
        year: Optional[int],
        method: str,
        industry_type: str = "general",
    ) -> dict:
        store = FactorStore(self.db_session, region=region, year=year, method=method)
        return store.get_factor(activity_type=activity_type, industry_type=industry_type)

    def calculate_emission(self, activity_record: dict, factor: dict) -> dict:
        amount = float(activity_record.get("amount", 0.0) or 0.0)
        factor_value = float(factor.get("value", 0.0) or 0.0)
        emission = round(amount * factor_value, 6)

        dq_x = str(activity_record.get("dq_activity_level", "C") or "C").upper()
        dq_f = str(factor.get("dq_factor_level", "C") or "C").upper()
        u_x = self.dqi_to_uncertainty.get(dq_x, 0.10)
        u_f = float(factor.get("gsd_factor", self.dqi_to_uncertainty.get(dq_f, 0.10)) or 0.10)

        return {
            "activity_id": activity_record.get("activity_id"),
            "activity_type": activity_record.get("activity_type", ""),
            "amount": amount,
            "unit": activity_record.get("unit", ""),
            "emission": emission,
            "u_x": u_x,
            "u_f": u_f,
            "factor_meta": factor,
        }

    def aggregate_emission(self, items: List[dict]) -> dict:
        total = round(sum(i.get("emission", 0.0) for i in items), 6)
        source_totals: Dict[str, float] = {}
        scope_totals: Dict[str, float] = {"S1": 0.0, "S2": 0.0, "S3": 0.0}

        for i in items:
            source = i.get("activity_type", "other")
            source_totals[source] = source_totals.get(source, 0.0) + i.get("emission", 0.0)
            scope = i.get("scope", "S3")
            scope_totals[scope] = scope_totals.get(scope, 0.0) + i.get("emission", 0.0)

        breakdown = []
        for source, emission in source_totals.items():
            ratio = emission / total if total > 0 else 0
            breakdown.append(
                {
                    "item": source,
                    "amount": 0.0,
                    "factor": 0.0,
                    "emission": round(emission, 4),
                    "unit": "kgCO2e",
                    "source": "aggregated",
                    "ratio": round(ratio, 4),
                }
            )
        breakdown = sorted(breakdown, key=lambda x: x["emission"], reverse=True)

        return {
            "total_emission": total,
            "source_breakdown": breakdown,
            "scope_breakdown": {k: round(v, 4) for k, v in scope_totals.items()},
        }

    def propagate_uncertainty(self, items: List[dict], mode: str = "analytic") -> dict:
        total = sum(i.get("emission", 0.0) for i in items)
        if total <= 0:
            return {"mode": mode, "ci95_low": 0.0, "ci95_high": 0.0, "relative_u": 0.0}

        # 当前阶段默认解析法，MC作为后续异步扩展。
        variance = 0.0
        for i in items:
            w = i.get("emission", 0.0) / total
            u_e = (i.get("u_x", 0.1) ** 2 + i.get("u_f", 0.1) ** 2) ** 0.5
            variance += (w * u_e) ** 2

        total_u = variance ** 0.5
        ci_low = max(0.0, total * (1 - 1.96 * total_u))
        ci_high = max(ci_low, total * (1 + 1.96 * total_u))
        return {
            "mode": "analytic" if mode not in {"analytic", "mc"} else mode,
            "ci95_low": round(ci_low, 4),
            "ci95_high": round(ci_high, 4),
            "relative_u": round(total_u, 6),
        }

    def build_carbon_flow_graph(self, source_breakdown: List[dict], stage_mapping: dict) -> dict:
        stage_totals = {
            "procurement": 0.0,
            "transport": 0.0,
            "storage": 0.0,
            "production": 0.0,
        }
        for row in source_breakdown:
            source = row.get("item", "")
            stage = stage_mapping.get(source, ("S3", None, "production"))[2]
            stage_totals[stage] = stage_totals.get(stage, 0.0) + float(row.get("emission", 0.0) or 0.0)

        return {
            "nodes": [
                {"name": "采购端"},
                {"name": "运输端"},
                {"name": "仓储端"},
                {"name": "生产端"},
                {"name": "排放端"},
            ],
            "links": [
                {"source": "采购端", "target": "运输端", "value": round(stage_totals.get("procurement", 0.0), 4)},
                {"source": "运输端", "target": "仓储端", "value": round(stage_totals.get("transport", 0.0), 4)},
                {"source": "仓储端", "target": "生产端", "value": round(stage_totals.get("storage", 0.0), 4)},
                {"source": "生产端", "target": "排放端", "value": round(stage_totals.get("production", 0.0) + stage_totals.get("transport", 0.0) + stage_totals.get("storage", 0.0) + stage_totals.get("procurement", 0.0), 4)},
            ],
        }

    def build_explain_trace(
        self,
        analysis_id: Optional[int],
        items: Optional[List[dict]] = None,
        benchmark_compare: Optional[dict] = None,
        uncertainty: Optional[dict] = None,
    ) -> dict:
        payload = {
            "analysis_id": analysis_id,
            "formula": "E_total = sum_i x_i * f(a_i, r_i, t_i, m_i)",
            "items": [],
            "benchmark": benchmark_compare or {},
            "uncertainty": uncertainty or {},
        }
        for i in (items or []):
            payload["items"].append(
                {
                    "activity_id": i.get("activity_id"),
                    "activity_type": i.get("activity_type"),
                    "scope": i.get("scope"),
                    "emission": i.get("emission"),
                    "factor": i.get("factor_meta", {}),
                }
            )
        return payload

    def build_carbon_flow(self, breakdown: list) -> dict:
        """输出Sankey可直接消费的碳流结构。"""
        transport = sum(i.get("emission", 0.0) for i in breakdown if i.get("item") in {"air_logistics", "reverse_logistics", "diesel"})
        storage = sum(i.get("emission", 0.0) for i in breakdown if i.get("item") in {"warehouse_energy", "electricity", "natural_gas"})
        package = sum(i.get("emission", 0.0) for i in breakdown if i.get("item") in {"packaging_waste", "waste"})

        total_mid = transport + storage + package
        if total_mid <= 0:
            total_mid = 0.0

        return {
            "nodes": [
                {"name": "采购端"},
                {"name": "运输端"},
                {"name": "仓储端"},
                {"name": "包装与废弃"},
                {"name": "碳排放"},
            ],
            "links": [
                {"source": "采购端", "target": "运输端", "value": round(transport, 2)},
                {"source": "采购端", "target": "仓储端", "value": round(storage, 2)},
                {"source": "采购端", "target": "包装与废弃", "value": round(package, 2)},
                {"source": "运输端", "target": "碳排放", "value": round(transport, 2)},
                {"source": "仓储端", "target": "碳排放", "value": round(storage, 2)},
                {"source": "包装与废弃", "target": "碳排放", "value": round(package, 2)},
            ],
            "total": round(total_mid, 2),
        }

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
