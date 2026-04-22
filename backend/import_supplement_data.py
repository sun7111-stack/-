"""
Import supplementary carbon-accounting demo data from docx_extracted.json.

Safety:
- Default mode is DRY RUN. It prints the import plan and rolls back.
- Use --apply only after reviewing the summary.

Run from repo root:
    python backend/import_supplement_data.py
    python backend/import_supplement_data.py --apply
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import SessionLocal, engine  # noqa: E402
from models.analysis import AnalysisBreakdown, AnalysisResult, RiskResult  # noqa: E402
from models.carbon import EmissionFactorItem, IndustryBenchmark  # noqa: E402
from models.data_pipeline import ActivityRecord, ParsedDataRecord, RawDataRecord  # noqa: E402
from models.enterprise import EnterpriseProfile  # noqa: E402
from models.esg import EsgScore  # noqa: E402
from models.finance import FinanceApplication  # noqa: F401,E402
from models.flow import EventStream, EvidenceChainRecord  # noqa: E402
from models.report import ContactMessage, Report  # noqa: F401,E402
from models.report_record import ReportRecord  # noqa: E402
from models.user import User  # noqa: E402
from utils.auth import hash_password  # noqa: E402


DOC_TABLES = [
    "enterprise_info",
    "raw_data_record",
    "parsed_data_record",
    "activity_record",
    "emission_factor_items",
    "analysis_results",
    "analysis_breakdowns",
    "industry_benchmarks",
    "esg_scores",
    "risk_results",
    "report_records",
    "event_stream",
    "evidence_chain_record",
]


def load_tables(path: Path) -> Dict[str, List[Dict[str, str]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tables: Dict[str, List[Dict[str, str]]] = {}
    for name, rows in zip(DOC_TABLES, data["tables"]):
        header = rows[0]
        tables[name] = [dict(zip(header, row)) for row in rows[1:]]
    return tables


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        text = str(value).strip().replace(",", "")
        if text in {"", "-", "None"}:
            return default
        return float(text)
    except Exception:
        return default


def parse_dt(value: str, fallback_date: str = "2026-04-22") -> datetime:
    value = (value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%H:%M"):
        try:
            dt = datetime.strptime(value, fmt)
            if fmt == "%H:%M":
                return datetime.strptime(f"{fallback_date} {value}:00", "%Y-%m-%d %H:%M:%S")
            return dt
        except ValueError:
            pass
    return datetime.now()


def normalize_risk_level(value: str) -> str:
    mapping = {"低": "low", "中": "medium", "高": "high", "极高": "critical", "低风险": "low", "中风险": "medium", "高风险": "high", "极高风险": "critical"}
    return mapping.get((value or "").strip(), value or "medium")


def event_status(value: str) -> str:
    return {"success": "done", "processing": "processing", "warning": "warning", "info": "info"}.get(value or "", value or "done")


def company_type_from_industry(industry: str) -> str:
    if "物流" in industry or "运输" in industry:
        return "logistics"
    if "软件" in industry or "信息" in industry:
        return "service"
    return "manufacture"


def user_email(external_id: str) -> str:
    if external_id == "E001":
        return "demo-e001@carbon-ai.com"
    if external_id == "E002":
        return "demo-e002@carbon-ai.com"
    return f"supplement-{external_id.lower()}@carbon.local"


def build_import(db, tables: Dict[str, List[Dict[str, str]]], apply: bool = False) -> Dict[str, int]:
    stats: Dict[str, int] = {}
    enterprise_user: Dict[str, User] = {}
    enterprise_profile: Dict[str, EnterpriseProfile] = {}
    raw_map: Dict[str, RawDataRecord] = {}
    parsed_map: Dict[str, ParsedDataRecord] = {}
    analysis_map: Dict[str, AnalysisResult] = {}

    # Existing E001/E002 mappings.
    for eid in ("E001", "E002"):
        user = db.query(User).filter(User.email == user_email(eid)).first()
        if user:
            enterprise_user[eid] = user
            profile = db.query(EnterpriseProfile).filter(EnterpriseProfile.user_id == user.id).first()
            if profile:
                enterprise_profile[eid] = profile

    # 1. Enterprises -> users + enterprise_profiles
    for row in tables["enterprise_info"]:
        eid = row["enterprise_id"]
        email = user_email(eid)
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                password_hash=hash_password("demo123") if apply else "DRY_RUN_PASSWORD_HASH",
                name=f"{row['enterprise_name']}管理员",
                company=row["enterprise_name"],
                company_type=company_type_from_industry(row["industry_type"]),
                phone=row.get("联系方式") or "",
            )
            db.add(user)
            db.flush()
            stats["users_inserted"] = stats.get("users_inserted", 0) + 1
        enterprise_user[eid] = user

        profile = db.query(EnterpriseProfile).filter(EnterpriseProfile.user_id == user.id).first()
        if not profile:
            profile = EnterpriseProfile(user_id=user.id)
            db.add(profile)
            stats["enterprise_profiles_inserted"] = stats.get("enterprise_profiles_inserted", 0) + 1
        profile.company_name = row["enterprise_name"]
        profile.industry = row["industry_type"]
        profile.company_scale = row["enterprise_scale"]
        profile.address = row["region_code"]
        profile.contact_person = row.get("联系人") or ""
        profile.contact_phone = row.get("联系方式") or ""
        profile.main_products = row.get("主要业务方向") or ""
        profile.established_date = row.get("created_at") or ""
        enterprise_profile[eid] = profile
    db.flush()

    # 2. Raw records
    for row in tables["raw_data_record"]:
        eid = row["enterprise_id"]
        profile = enterprise_profile.get(eid)
        existing = db.query(RawDataRecord).filter(RawDataRecord.file_path == row["file_path"]).first()
        rec = existing or RawDataRecord()
        rec.enterprise_id = profile.id if profile else None
        rec.data_type = row["data_type"]
        rec.file_name = row["file_name"]
        rec.file_path = row["file_path"]
        rec.upload_time = parse_dt(row["upload_time"])
        rec.parse_status = "parsed" if row["parse_status"] == "success" else row["parse_status"]
        if not existing:
            db.add(rec)
            stats["raw_data_record_inserted"] = stats.get("raw_data_record_inserted", 0) + 1
        raw_map[row["raw_data_id"]] = rec
    db.flush()

    # 3. Parsed records
    for row in tables["parsed_data_record"]:
        raw = raw_map.get(row["raw_data_id"])
        if not raw:
            continue
        existing = (
            db.query(ParsedDataRecord)
            .filter(
                ParsedDataRecord.raw_data_id == raw.id,
                ParsedDataRecord.parsed_field_name == row["parsed_field_name"],
                ParsedDataRecord.parsed_field_value == row["parsed_field_value"],
            )
            .first()
        )
        rec = existing or ParsedDataRecord(raw_data_id=raw.id)
        rec.raw_field_name = row["raw_field_name"]
        rec.raw_field_value = row["raw_field_value"]
        rec.parsed_field_name = row["parsed_field_name"]
        rec.parsed_field_value = row["parsed_field_value"]
        rec.confidence_score = as_float(row["confidence_score"])
        if not existing:
            db.add(rec)
            stats["parsed_data_record_inserted"] = stats.get("parsed_data_record_inserted", 0) + 1
        parsed_map[row["parsed_id"]] = rec
    db.flush()

    # Manual placeholder parsed rows for activities without OCR parsed_id.
    def manual_parsed_for(eid: str, activity_type: str, amount: str) -> ParsedDataRecord:
        raw = next((r for ext, r in raw_map.items() if ext.startswith("R") and r.enterprise_id == enterprise_profile[eid].id), None)
        if raw is None:
            raw = RawDataRecord(enterprise_id=enterprise_profile[eid].id, data_type="manual", file_name=f"{eid}_manual.xlsx", file_path=f"/demo/files/{eid.lower()}_manual.xlsx", parse_status="parsed")
            db.add(raw)
            db.flush()
        rec = ParsedDataRecord(raw_data_id=raw.id, raw_field_name="manual_input", raw_field_value=amount, parsed_field_name=activity_type, parsed_field_value=amount, confidence_score=1.0)
        db.add(rec)
        db.flush()
        stats["manual_parsed_created"] = stats.get("manual_parsed_created", 0) + 1
        return rec

    # 4. Activities
    for row in tables["activity_record"]:
        eid = row["enterprise_id"]
        profile = enterprise_profile.get(eid)
        if not profile:
            continue
        existing = (
            db.query(ActivityRecord)
            .filter(ActivityRecord.enterprise_id == profile.id, ActivityRecord.activity_type == row["activity_type"], ActivityRecord.period_time == row["period_time"], ActivityRecord.activity_amount == as_float(row["activity_amount"]))
            .first()
        )
        parsed = parsed_map.get(row["parsed_id"])
        if parsed is None:
            if existing:
                parsed = db.query(ParsedDataRecord).filter(ParsedDataRecord.id == existing.parsed_id).first()
            if parsed is None:
                parsed = manual_parsed_for(eid, row["activity_type"], row["activity_amount"])
        rec = existing or ActivityRecord(enterprise_id=profile.id, parsed_id=parsed.id)
        rec.activity_type = row["activity_type"]
        rec.activity_amount = as_float(row["activity_amount"])
        rec.activity_unit = row["activity_unit"]
        rec.amount_raw = rec.activity_amount
        rec.unit_raw = rec.activity_unit
        rec.region_code = row["region_code"]
        rec.period_time = row["period_time"]
        rec.clean_status = row["clean_status"]
        rec.scope = "S2" if "electricity" in rec.activity_type or "energy" in rec.activity_type or "storage" in rec.activity_type else ("S1" if "gas" in rec.activity_type or "fuel" in rec.activity_type or "coal" in rec.activity_type else "S3")
        if not existing:
            db.add(rec)
            stats["activity_record_inserted"] = stats.get("activity_record_inserted", 0) + 1
    db.flush()

    # 5. Factors
    for row in tables["emission_factor_items"]:
        existing = (
            db.query(EmissionFactorItem)
            .filter(EmissionFactorItem.activity_type == row["activity_type"], EmissionFactorItem.region == row["region_code"], EmissionFactorItem.year == int(row["version_year"]))
            .first()
        )
        rec = existing or EmissionFactorItem(activity_type=row["activity_type"], region=row["region_code"], year=int(row["version_year"]))
        rec.factor_value = as_float(row["factor_value"])
        rec.factor_unit = row["factor_unit"]
        rec.source = row["source_desc"]
        rec.version = f"{row['version_year']}-supplement"
        rec.version_tag = f"supplement-{row['factor_id']}"
        rec.method = "default"
        rec.source_type = "supplement_factor"
        rec.description = f"补充数据原始ID: {row['factor_id']}"
        if not existing:
            db.add(rec)
            stats["emission_factor_items_inserted"] = stats.get("emission_factor_items_inserted", 0) + 1

    # 8. Benchmarks (pivot metric rows into one schema row per industry)
    grouped: Dict[str, Dict[str, str]] = {}
    for row in tables["industry_benchmarks"]:
        grouped.setdefault(row["industry_type"], {})[row["metric_name"]] = row["benchmark_value"]
    for industry, values in grouped.items():
        existing = db.query(IndustryBenchmark).filter(IndustryBenchmark.industry == industry).first()
        rec = existing or IndustryBenchmark(industry=industry, industry_cn=industry)
        rec.industry_cn = industry
        rec.carbon_per_revenue = as_float(values.get("carbon_intensity_avg"))
        rec.energy_metric = as_float(values.get("total_emission_avg"))
        if not existing:
            db.add(rec)
            stats["industry_benchmarks_inserted"] = stats.get("industry_benchmarks_inserted", 0) + 1
    db.flush()

    # 6. Analysis
    for row in tables["analysis_results"]:
        user = enterprise_user.get(row["enterprise_id"])
        company = user.company if user else row["enterprise_id"]
        existing = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.enterprise_name == company, AnalysisResult.analysis_time == parse_dt(row["analysis_time"]))
            .first()
        )
        rec = existing or AnalysisResult(user_id=user.id if user else 1, enterprise_name=company)
        rec.analysis_time = parse_dt(row["analysis_time"])
        rec.total_emission = as_float(row["total_emission"])
        rec.carbon_intensity = as_float(row["carbon_intensity"])
        rec.industry_deviation = as_float(row["industry_deviation"])
        rec.risk_level = normalize_risk_level(row["risk_level"])
        rec.major_source = row["major_source"]
        rec.advice_text = row["advice_text"]
        if not existing:
            db.add(rec)
            stats["analysis_results_inserted"] = stats.get("analysis_results_inserted", 0) + 1
        analysis_map[row["analysis_id"]] = rec
    db.flush()

    # 7. Breakdowns
    for row in tables["analysis_breakdowns"]:
        analysis = analysis_map.get(row["analysis_id"])
        if not analysis:
            continue
        existing = db.query(AnalysisBreakdown).filter(AnalysisBreakdown.analysis_id == analysis.id, AnalysisBreakdown.source_type == row["source_type"]).first()
        if not existing:
            db.add(AnalysisBreakdown(analysis_id=analysis.id, source_type=row["source_type"], emission_value=as_float(row["emission_value"]), proportion=as_float(row["proportion"])))
            stats["analysis_breakdowns_inserted"] = stats.get("analysis_breakdowns_inserted", 0) + 1

    # 9. ESG
    for row in tables["esg_scores"]:
        user = enterprise_user.get(row["enterprise_id"])
        if not user:
            continue
        existing = db.query(EsgScore).filter(EsgScore.user_id == user.id).first()
        if not existing:
            db.add(EsgScore(user_id=user.id, environment=as_float(row["environment_score"]), social=as_float(row["social_score"]), governance=as_float(row["governance_score"]), total=as_float(row["total_score"]), recommendations=[row.get("comment_text", "")]))
            stats["esg_scores_inserted"] = stats.get("esg_scores_inserted", 0) + 1

    # 10. Risks
    for row in tables["risk_results"]:
        user = enterprise_user.get(row["enterprise_id"])
        analysis = analysis_map.get(row["analysis_id"])
        if not user:
            continue
        existing = db.query(RiskResult).filter(RiskResult.user_id == user.id, RiskResult.analysis_id == (analysis.id if analysis else None), RiskResult.risk_score == as_float(row["risk_score"])).first()
        if not existing:
            db.add(RiskResult(user_id=user.id, analysis_id=analysis.id if analysis else None, risk_score=as_float(row["risk_score"]), risk_level=normalize_risk_level(row["risk_level"]), risk_reason=row["risk_reason"], risk_advice=row["risk_advice"]))
            stats["risk_results_inserted"] = stats.get("risk_results_inserted", 0) + 1

    # 11. Reports
    for row in tables["report_records"]:
        analysis = analysis_map.get(row["analysis_id"])
        user_id = analysis.user_id if analysis else 1
        existing = db.query(ReportRecord).filter(ReportRecord.report_title == row["report_title"]).first()
        if not existing:
            db.add(ReportRecord(user_id=user_id, analysis_id=str(analysis.id if analysis else row["analysis_id"]), report_type=row["report_type"], report_title=row["report_title"], generate_time=parse_dt(row["generate_time"]), export_status=row["export_status"], file_path=row["file_path"], report_context={"external_report_id": row["report_id"]}, report_preview={}))
            stats["report_records_inserted"] = stats.get("report_records_inserted", 0) + 1

    # 12. Events
    for row in tables["event_stream"]:
        existing = db.query(EventStream).filter(EventStream.enterprise_name == row["enterprise_name"], EventStream.event_desc == row["event_desc"]).first()
        if not existing:
            db.add(EventStream(enterprise_name=row["enterprise_name"], event_type=row["event_type"], event_desc=row["event_desc"], event_time=parse_dt(row["event_time"]), event_status=event_status(row["event_status"])))
            stats["event_stream_inserted"] = stats.get("event_stream_inserted", 0) + 1

    # 13. Evidence chain
    for row in tables["evidence_chain_record"]:
        analysis = analysis_map.get(row["analysis_id"])
        analysis_id = str(analysis.id if analysis else row["analysis_id"])
        hash_value = "" if row["hash_value"] == "-" else row["hash_value"]
        existing = db.query(EvidenceChainRecord).filter(EvidenceChainRecord.analysis_id == analysis_id, EvidenceChainRecord.step_name == row["step_name"], EvidenceChainRecord.timestamp == parse_dt(row["timestamp"])).first()
        if not existing:
            db.add(EvidenceChainRecord(raw_data_id=row["raw_data_id"], analysis_id=analysis_id, step_name=row["step_name"], hash_value=hash_value, timestamp=parse_dt(row["timestamp"]), chain_status=row["chain_status"], meta_payload={"external_evidence_id": row["evidence_id"], "external_analysis_id": row["analysis_id"]}))
            stats["evidence_chain_record_inserted"] = stats.get("evidence_chain_record_inserted", 0) + 1

    db.flush()
    return stats


def main() -> None:
    # Keep dry-run output readable even when APP_DEBUG=True in .env.
    engine.echo = False
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=str(ROOT / "docx_extracted.json"))
    parser.add_argument("--apply", action="store_true", help="Actually commit data to MySQL")
    args = parser.parse_args()

    tables = load_tables(Path(args.json))
    print("Loaded document tables:")
    for name in DOC_TABLES:
        print(f"  - {name}: {len(tables[name])} rows")

    db = SessionLocal()
    try:
        stats = build_import(db, tables, apply=args.apply)
        print("\nImport plan:")
        for key in sorted(stats):
            print(f"  - {key}: {stats[key]}")
        if args.apply:
            db.commit()
            print("\nAPPLIED: data committed to database.")
        else:
            db.rollback()
            print("\nDRY RUN ONLY: no database changes were committed. Re-run with --apply to import.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
