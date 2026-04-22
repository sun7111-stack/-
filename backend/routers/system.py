"""System readiness endpoints for the API-backed real mode."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from database import get_db
from models.analysis import AnalysisResult, RiskResult
from models.carbon import EmissionFactor, EmissionFactorItem, IndustryBenchmark
from models.data_pipeline import ActivityRecord, ParsedDataRecord, RawDataRecord
from models.flow import (
    EventStream,
    EvidenceAnchor,
    EvidenceChainRecord,
    EvidenceChainStep,
    EvidenceObject,
    EvidenceProof,
)
from models.report_record import ReportRecord
from models.user import User

router = APIRouter(prefix="/api/system", tags=["system"])


def _count(db: Session, model) -> int:
    return int(db.query(func.count(model.id)).scalar() or 0)


def _check(
    checks: List[Dict[str, Any]],
    key: str,
    name: str,
    ok: bool,
    detail: str,
    *,
    required: bool = True,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    checks.append(
        {
            "key": key,
            "name": name,
            "ok": bool(ok),
            "required": required,
            "detail": detail,
            "meta": meta or {},
        }
    )


@router.get("/real-mode-health", summary="Real mode readiness check")
def real_mode_health(db: Session = Depends(get_db)):
    """Return a read-only readiness report for the API-backed real workflow.

    This endpoint intentionally does not create demo data. It answers one
    practical question for the frontend: can the real flow run now, and if not,
    which dependency should the teammate fix first?
    """

    checks: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}

    try:
        db.execute(text("SELECT 1"))
        counts.update(
            {
                "users": _count(db, User),
                "raw_data_record": _count(db, RawDataRecord),
                "parsed_data_record": _count(db, ParsedDataRecord),
                "activity_record": _count(db, ActivityRecord),
                "analysis_results": _count(db, AnalysisResult),
                "risk_results": _count(db, RiskResult),
                "event_stream": _count(db, EventStream),
            }
        )
        _check(
            checks,
            "database",
            "数据库",
            True,
            "连接正常，核心业务表可读取",
            meta=counts,
        )
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        _check(checks, "database", "数据库", False, f"数据库不可用：{exc}")

    try:
        factor_count = _count(db, EmissionFactor) + _count(db, EmissionFactorItem)
        benchmark_count = _count(db, IndustryBenchmark)
        counts["emission_factors"] = factor_count
        counts["industry_benchmarks"] = benchmark_count
        _check(
            checks,
            "factor_library",
            "排放因子库",
            factor_count > 0 and benchmark_count > 0,
            f"因子 {factor_count} 条，行业基准 {benchmark_count} 条",
            meta={"factor_count": factor_count, "benchmark_count": benchmark_count},
        )
    except Exception as exc:  # pragma: no cover
        _check(checks, "factor_library", "排放因子库", False, f"因子库读取失败：{exc}")

    try:
        from services.vlm_parser import DASHSCOPE_AVAILABLE, settings as ocr_settings

        mock_mode = bool(ocr_settings.USE_MOCK)
        has_key = bool(ocr_settings.DASHSCOPE_API_KEY)
        _check(
            checks,
            "ocr",
            "OCR/VLM",
            True,
            "真实 VLM 可用" if not mock_mode else "当前为 OCR mock/降级模式，仍可跑通样例闭环",
            required=False,
            meta={
                "mock_mode": mock_mode,
                "dashscope_available": bool(DASHSCOPE_AVAILABLE),
                "api_key_configured": has_key,
                "supported_types": ocr_settings.SUPPORTED_TYPES,
            },
        )
    except Exception as exc:  # pragma: no cover
        _check(checks, "ocr", "OCR/VLM", False, f"OCR 模块不可用：{exc}", required=False)

    try:
        evidence_counts = {
            "evidence_chain_record": _count(db, EvidenceChainRecord),
            "evidence_object": _count(db, EvidenceObject),
            "evidence_chain_step": _count(db, EvidenceChainStep),
            "evidence_anchor": _count(db, EvidenceAnchor),
            "evidence_proof": _count(db, EvidenceProof),
        }
        counts.update(evidence_counts)
        chain_ready = evidence_counts["evidence_chain_step"] >= 0
        _check(
            checks,
            "evidence_chain",
            "证据链",
            chain_ready,
            "证据链表结构可读，可执行存证与校验",
            meta=evidence_counts,
        )
    except Exception as exc:  # pragma: no cover
        _check(checks, "evidence_chain", "证据链", False, f"证据链不可用：{exc}")

    try:
        from services.report_llm import report_generator

        report_count = _count(db, ReportRecord)
        counts["report_records"] = report_count
        _check(
            checks,
            "report_service",
            "报告服务",
            True,
            "Qwen 可用" if not report_generator.mock_mode else "报告服务处于 mock/降级生成模式",
            required=False,
            meta={"mock_mode": bool(report_generator.mock_mode), "report_records": report_count},
        )
    except Exception as exc:  # pragma: no cover
        _check(checks, "report_service", "报告服务", False, f"报告服务不可用：{exc}", required=False)

    required_ok = all(item["ok"] for item in checks if item["required"])
    optional_warnings = [item for item in checks if not item["required"] and not item["ok"]]
    degraded = [
        item
        for item in checks
        if not item["required"]
        and item["ok"]
        and item.get("meta", {}).get("mock_mode") is True
    ]

    if not required_ok:
        status = "blocked"
    elif optional_warnings or degraded:
        status = "warning"
    else:
        status = "ok"

    return {
        "status": status,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "checks": checks,
        "counts": counts,
        "message": {
            "ok": "真实模式依赖已就绪",
            "warning": "真实闭环可运行，但存在 mock/降级服务",
            "blocked": "真实模式关键依赖未就绪",
        }[status],
    }
