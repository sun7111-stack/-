"""一键导入演示种子数据。

用法:
    python import_demo_seed.py
    python import_demo_seed.py --create-tables
    python import_demo_seed.py --sql-file demo_seed_data.sql

说明:
- 默认读取当前目录下的 demo_seed_data.sql。
- 会按语句逐条执行，适合 MySQL / MariaDB。
- 如果你想先建表再导数，可加 --create-tables。
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

from sqlalchemy import text

from database import Base, engine

# 导入模型以注册到 Base.metadata，供 --create-tables 使用
from models.user import User  # noqa: F401
from models.carbon import EmissionFactor, IndustryBenchmark, CarbonRecord, EmissionFactorItem  # noqa: F401
from models.esg import EsgScore  # noqa: F401
from models.finance import FinancialProduct, FinanceApplication  # noqa: F401
from models.report import Report, Policy, CaseStudy, ContactMessage  # noqa: F401
from models.trace import DataTraceRecord  # noqa: F401
from models.enterprise import EnterpriseProfile, EnterpriseCertification, EnterpriseActivity  # noqa: F401
from models.data_upload import DataUpload, ApplicationMaterial  # noqa: F401
from models.flow import EventStream, EvidenceChainRecord, EvidenceObject, EvidenceChainStep, EvidenceAnchor, EvidenceProof, TrustScoreRecord  # noqa: F401
from models.report_record import ReportRecord  # noqa: F401
from models.analysis import AnalysisResult, AnalysisBreakdown, RiskResult  # noqa: F401
from models.data_pipeline import RawDataRecord, ParsedDataRecord, ActivityRecord  # noqa: F401
from models.factor_match_log import FactorMatchLog  # noqa: F401
from models.analysis_v2 import AnalysisResultV2Snapshot  # noqa: F401


DEFAULT_SQL_FILE = Path(__file__).with_name("demo_seed_data.sql")


def _strip_sql_comments(lines: Iterable[str]) -> str:
    kept: List[str] = []
    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("--"):
            continue
        if stripped.startswith("/*") and stripped.endswith("*/"):
            continue
        kept.append(line)
    return "\n".join(kept)


def _split_sql_statements(sql_text: str) -> List[str]:
    statements: List[str] = []
    current: List[str] = []
    in_single = False
    in_double = False
    escape = False

    for char in sql_text:
        if escape:
            current.append(char)
            escape = False
            continue

        if char == "\\":
            current.append(char)
            escape = True
            continue

        if char == "'" and not in_double:
            in_single = not in_single
            current.append(char)
            continue

        if char == '"' and not in_single:
            in_double = not in_double
            current.append(char)
            continue

        if char == ";" and not in_single and not in_double:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            continue

        current.append(char)

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def run_sql_file(sql_file: Path) -> None:
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL 文件不存在: {sql_file}")

    raw_text = sql_file.read_text(encoding="utf-8-sig")
    cleaned_text = _strip_sql_comments(raw_text.splitlines())
    statements = _split_sql_statements(cleaned_text)

    if not statements:
        print("未检测到可执行 SQL 语句。")
        return

    with engine.begin() as connection:
        for index, statement in enumerate(statements, start=1):
            connection.execute(text(statement))
            print(f"[OK] {index}/{len(statements)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导入演示种子数据")
    parser.add_argument("--sql-file", default=str(DEFAULT_SQL_FILE), help="SQL 文件路径，默认 demo_seed_data.sql")
    parser.add_argument("--create-tables", action="store_true", help="先创建所有表")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sql_file = Path(args.sql_file)

    if args.create_tables:
        print("正在创建表结构...")
        create_tables()
        print("表结构创建完成。")

    print(f"正在导入种子数据: {sql_file}")
    run_sql_file(sql_file)
    print("导入完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
