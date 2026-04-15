"""OCR后数据治理服务：字段映射、单位统一、合法性校验、标准化活动记录生成。"""
from typing import Any, Dict, List, Tuple


FIELD_MAP = {
    "amount": "activity_amount",
    "value": "activity_amount",
    "distance": "distance_km",
    "weight": "weight_ton",
    "vendor": "supplier_name",
    "period": "period_time",
    "unit": "activity_unit",
}

UNIT_MAP = {
    "度": "kWh",
    "千瓦时": "kWh",
    "kwh": "kWh",
    "公里": "km",
    "km": "km",
    "吨": "t",
    "吨公里": "t·km",
    "ton-km": "t·km",
    "m3": "m3",
    "l": "L",
}


def map_fields(fields: Dict[str, Any]) -> List[Dict[str, Any]]:
    mapped: List[Dict[str, Any]] = []
    for key, value in fields.items():
        mapped.append(
            {
                "raw_field_name": key,
                "raw_field_value": value,
                "parsed_field_name": FIELD_MAP.get(key, key),
                "parsed_field_value": value,
            }
        )
    return mapped


def normalize_units(fields: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(fields)
    unit = str(normalized.get("unit", normalized.get("activity_unit", ""))).strip()
    if unit:
        normalized["activity_unit"] = UNIT_MAP.get(unit.lower(), UNIT_MAP.get(unit, unit))
    else:
        normalized["activity_unit"] = ""
    return normalized


def validate_record(fields: Dict[str, Any]) -> Tuple[bool, List[str]]:
    warnings: List[str] = []
    amount = fields.get("amount", fields.get("value", fields.get("activity_amount", 0)))
    try:
        amount_val = float(amount)
    except (TypeError, ValueError):
        amount_val = 0.0

    if amount_val < 0:
        warnings.append("数值不能为负")
    if amount_val == 0:
        warnings.append("缺少有效活动量，已按0处理")
    if amount_val > 10_000_000:
        warnings.append("检测到异常大值，请人工复核")

    return len(warnings) == 0, warnings


def build_activity_record(
    enterprise_id: str,
    suggested_activity_type: str,
    normalized_fields: Dict[str, Any],
    valid: bool,
    warnings: List[str],
) -> Dict[str, Any]:
    amount = normalized_fields.get("amount", normalized_fields.get("value", 0))
    try:
        amount_val = float(amount)
    except (TypeError, ValueError):
        amount_val = 0.0

    return {
        "enterprise_id": enterprise_id,
        "activity_type": suggested_activity_type,
        "activity_amount": amount_val,
        "activity_unit": normalized_fields.get("activity_unit", normalized_fields.get("unit", "")),
        "period_time": normalized_fields.get("period", normalized_fields.get("period_time", "")),
        "clean_status": "clean" if valid else "warning",
        "warnings": warnings,
    }


def govern_parsed_result(result_data: Dict[str, Any], enterprise_id: str = "demo-enterprise") -> Dict[str, Any]:
    fields = result_data.get("fields", {}) or {}
    mapped = map_fields(fields)
    normalized = normalize_units(fields)
    valid, warnings = validate_record(normalized)
    cleaned = build_activity_record(
        enterprise_id=enterprise_id,
        suggested_activity_type=result_data.get("suggested_activity_type", "waste"),
        normalized_fields=normalized,
        valid=valid,
        warnings=warnings,
    )

    return {
        "raw_data": {
            "doc_type": result_data.get("doc_type", "unknown"),
            "raw_text": result_data.get("raw_text", ""),
        },
        "parsed_data": fields,
        "mapped_data": mapped,
        "normalized_data": normalized,
        "cleaned_record": cleaned,
    }
