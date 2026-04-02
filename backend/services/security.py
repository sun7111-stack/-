"""数据哈希确权与留痕服务"""
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Tuple

from sqlalchemy.orm import Session

from models.trace import DataTraceRecord


def generate_data_hash(
    raw_text: str,
    structured_fields: Dict[str, Any],
    user_id: int,
    timestamp: datetime = None,
) -> Tuple[str, datetime]:
    """对关键字段生成稳定 sha256 哈希。"""
    if timestamp is None:
        timestamp = datetime.now()

    payload = {
        "raw_text": raw_text,
        "structured_fields": structured_fields,
        "user_id": user_id,
        "timestamp": timestamp.isoformat(),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return digest, timestamp


def save_data_trace(
    db: Session,
    raw_text: str,
    structured_fields: Dict[str, Any],
    user_id: int,
    bill_id: str,
    doc_type: str,
) -> DataTraceRecord:
    """保存数据确权记录。"""
    data_hash, timestamp = generate_data_hash(raw_text, structured_fields, user_id)
    record = DataTraceRecord(
        bill_id=bill_id,
        user_id=user_id,
        doc_type=doc_type,
        data_hash=data_hash,
        raw_text=raw_text,
        structured_data=structured_fields,
        created_at=timestamp,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
