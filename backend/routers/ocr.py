from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.enterprise import EnterpriseProfile
from models.data_pipeline import RawDataRecord, ParsedDataRecord, ActivityRecord
from services.vlm_parser import parse_document_wrapper, settings
from services.data_governance import govern_parsed_result
from services.security import save_data_trace
from utils.auth import get_current_user_optional

router = APIRouter(prefix='/api/ocr', tags=['OCR票据识别'])

# ================== 数据模型 (Schemas) ==================
class OCRParseResult(BaseModel):
    doc_type: str = Field(..., description="票据类型枚举")
    confidence: float = Field(..., ge=0, le=1, description="识别置信度")
    fields: Dict[str, Any] = Field(..., description="结构化关键字段")
    raw_text: str = Field(..., description="原始文本(存证用)")
    suggested_activity_type: str = Field(..., description="碳核算活动类型")
    raw_data: Optional[Dict[str, Any]] = None
    parsed_data: Optional[Dict[str, Any]] = None
    mapped_data: Optional[list] = None
    normalized_data: Optional[Dict[str, Any]] = None
    cleaned_record: Optional[Dict[str, Any]] = None
    chain_ids: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    # P0新增：复杂票据兜底字段
    parse_method: Optional[str] = Field(None, description="解析方法(mock/simple_heuristic/vlm_advanced)")
    complexity: Optional[str] = Field(None, description="文档复杂度(simple/standard/complex)")
    complexity_notes: Optional[str] = Field(None, description="复杂度相关说明")
    parse_warning: Optional[str] = Field(None, description="解析警告或降级信息")

class OCRResponse(BaseModel):
    success: bool
    data: Optional[OCRParseResult] = None
    message: str = ""


class OCRChainCheckResponse(BaseModel):
    success: bool
    raw_data: Optional[Dict[str, Any]] = None
    parsed_data: List[Dict[str, Any]] = []
    activity_data: List[Dict[str, Any]] = []
    message: str = ""


class OCRChainOverviewResponse(BaseModel):
    success: bool
    total_count: int
    completed_count: int
    completion_rate: float
    records: List[Dict[str, Any]] = []
    message: str = ""

@router.get('/health', summary='健康检查与模式探测')
async def health_check():
    return {
        "status": "ok",
        "mock_mode": settings.USE_MOCK,
        "message": "碳融智核OCR服务运行正常"
    }

@router.post('/recognize', response_model=OCRResponse, summary='票据结构化识别')
async def recognize(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    # 1. 校验
    if file.content_type not in settings.SUPPORTED_TYPES:
        raise HTTPException(status_code=400, detail="文件格式不支持，仅支持JPG/PNG/PDF")

    # 读取一次检查大小
    content = await file.read()
    if len(content) > settings.MAX_SIZE:
        raise HTTPException(status_code=400, detail=f"文件过大，最大支持 {settings.MAX_SIZE / 1024 / 1024} MB")
    await file.seek(0)  # 重置指针

    # 2. 调用业务逻辑
    try:
        # 2.1 创建原始凭证记录（raw_data_record）
        enterprise_id = None
        if current_user is not None:
            profile = db.query(EnterpriseProfile).filter(EnterpriseProfile.user_id == current_user.id).first()
            if profile is not None:
                enterprise_id = profile.id

        raw_record = RawDataRecord(
            enterprise_id=enterprise_id,
            data_type=file.content_type or "",
            file_name=file.filename or "",
            file_path=f"/uploads/{file.filename or ''}",
            parse_status="processing",
        )
        db.add(raw_record)
        db.flush()

        result_data = await parse_document_wrapper(file)
        governance = govern_parsed_result(
            result_data=result_data,
            enterprise_id=str(enterprise_id or "demo-enterprise"),
        )
        result_data.update(governance)

        # 2.2 写入解析字段记录（parsed_data_record）
        parsed_rows = []
        for row in result_data.get("mapped_data", []) or []:
            parsed_row = ParsedDataRecord(
                raw_data_id=raw_record.id,
                raw_field_name=str(row.get("raw_field_name", "")),
                raw_field_value=str(row.get("raw_field_value", "")),
                parsed_field_name=str(row.get("parsed_field_name", "")),
                parsed_field_value=str(row.get("parsed_field_value", "")),
                confidence_score=float(result_data.get("confidence", 0.0) or 0.0),
            )
            db.add(parsed_row)
            parsed_rows.append(parsed_row)

        db.flush()

        # 2.3 写入标准化活动记录（activity_record）
        cleaned = result_data.get("cleaned_record", {}) or {}
        parsed_anchor = parsed_rows[0] if parsed_rows else None
        if parsed_anchor is not None:
            activity_row = ActivityRecord(
                enterprise_id=enterprise_id,
                parsed_id=parsed_anchor.id,
                activity_type=str(cleaned.get("activity_type", result_data.get("suggested_activity_type", "waste"))),
                activity_amount=float(cleaned.get("activity_amount", 0.0) or 0.0),
                activity_unit=str(cleaned.get("activity_unit", "")),
                region_code=str((result_data.get("fields", {}) or {}).get("region_code", "全国") or "全国"),
                period_time=str(cleaned.get("period_time", "")),
                clean_status=str(cleaned.get("clean_status", "warning")),
            )
            db.add(activity_row)
            db.flush()
            activity_id = activity_row.id
        else:
            activity_id = None

        raw_record.parse_status = "parsed"
        db.commit()

        result_data["chain_ids"] = {
            "raw_data_id": raw_record.id,
            "parsed_ids": [r.id for r in parsed_rows],
            "activity_id": activity_id,
        }

        try:
            save_data_trace(
                db=db,
                raw_text=result_data.get("raw_text", ""),
                structured_fields=result_data.get("fields", {}),
                user_id=current_user.id if current_user else 0,
                bill_id=f"ocr-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                doc_type=result_data.get("doc_type", "unknown"),
            )
        except Exception:
            # 留痕失败不影响主识别流程
            pass

        return OCRResponse(
            success=True,
            data=OCRParseResult(**result_data),
            message="识别成功"
        )
    except Exception as e:
        db.rollback()
        return OCRResponse(
            success=False,
            message=f"识别失败: {str(e)}"
        )


@router.get('/sample/{doc_type}', summary='获取示例识别结果')
async def get_sample(doc_type: str):
    samples = {
        "electricity": {
            "doc_type": "electricity_bill",
            "confidence": 0.96,
            "fields": {"amount": 1320, "unit": "kWh", "period": "2026-03", "vendor": "华东电网"},
            "raw_text": "电费单示例文本",
            "suggested_activity_type": "electricity",
        },
        "logistics": {
            "doc_type": "logistics_bill",
            "confidence": 0.94,
            "fields": {"distance": 980, "weight": 2.1, "unit": "吨公里", "vendor": "顺丰"},
            "raw_text": "物流单示例文本",
            "suggested_activity_type": "air_logistics",
        },
        "fuel": {
            "doc_type": "fuel_bill",
            "confidence": 0.93,
            "fields": {"amount": 420, "unit": "L", "period": "2026-03", "vendor": "中石化"},
            "raw_text": "燃料单示例文本",
            "suggested_activity_type": "diesel",
        },
    }
    payload = samples.get(doc_type, samples["electricity"])
    payload.update(govern_parsed_result(payload))
    return OCRResponse(success=True, data=OCRParseResult(**payload), message="示例返回成功")


@router.get('/chain-check/{raw_data_id}', response_model=OCRChainCheckResponse, summary='上传解析链路核验')
def chain_check(
    raw_data_id: int,
    db: Session = Depends(get_db),
):
    raw_row = db.query(RawDataRecord).filter(RawDataRecord.id == raw_data_id).first()
    if raw_row is None:
        return OCRChainCheckResponse(
            success=False,
            message="未找到对应 raw_data_record",
        )

    parsed_rows = (
        db.query(ParsedDataRecord)
        .filter(ParsedDataRecord.raw_data_id == raw_data_id)
        .order_by(ParsedDataRecord.id.asc())
        .all()
    )
    parsed_ids = [p.id for p in parsed_rows]

    activity_rows = []
    if parsed_ids:
        activity_rows = (
            db.query(ActivityRecord)
            .filter(ActivityRecord.parsed_id.in_(parsed_ids))
            .order_by(ActivityRecord.id.asc())
            .all()
        )

    return OCRChainCheckResponse(
        success=True,
        raw_data={
            "id": raw_row.id,
            "enterprise_id": raw_row.enterprise_id,
            "data_type": raw_row.data_type,
            "file_name": raw_row.file_name,
            "file_path": raw_row.file_path,
            "upload_time": raw_row.upload_time.isoformat() if raw_row.upload_time else "",
            "parse_status": raw_row.parse_status,
        },
        parsed_data=[
            {
                "id": p.id,
                "raw_data_id": p.raw_data_id,
                "raw_field_name": p.raw_field_name,
                "raw_field_value": p.raw_field_value,
                "parsed_field_name": p.parsed_field_name,
                "parsed_field_value": p.parsed_field_value,
                "confidence_score": p.confidence_score,
                "created_at": p.created_at.isoformat() if p.created_at else "",
            }
            for p in parsed_rows
        ],
        activity_data=[
            {
                "id": a.id,
                "enterprise_id": a.enterprise_id,
                "parsed_id": a.parsed_id,
                "activity_type": a.activity_type,
                "activity_amount": a.activity_amount,
                "activity_unit": a.activity_unit,
                "region_code": a.region_code,
                "period_time": a.period_time,
                "clean_status": a.clean_status,
                "created_at": a.created_at.isoformat() if a.created_at else "",
            }
            for a in activity_rows
        ],
        message="链路核验完成",
    )


@router.get('/chain-overview', response_model=OCRChainOverviewResponse, summary='上传解析链路总览')
def chain_overview(
    limit: int = 10,
    enterprise_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    safe_limit = max(1, min(limit, 100))
    query = db.query(RawDataRecord)
    if enterprise_id is not None:
        query = query.filter(RawDataRecord.enterprise_id == enterprise_id)

    raw_rows = query.order_by(RawDataRecord.id.desc()).limit(safe_limit).all()

    records: List[Dict[str, Any]] = []
    completed_count = 0

    for raw in raw_rows:
        parsed_rows = (
            db.query(ParsedDataRecord.id)
            .filter(ParsedDataRecord.raw_data_id == raw.id)
            .all()
        )
        parsed_ids = [row.id for row in parsed_rows]
        parsed_count = len(parsed_ids)

        activity_count = 0
        if parsed_ids:
            activity_count = (
                db.query(ActivityRecord)
                .filter(ActivityRecord.parsed_id.in_(parsed_ids))
                .count()
            )

        is_completed = parsed_count > 0 and activity_count > 0 and raw.parse_status == "parsed"
        if is_completed:
            completed_count += 1

        records.append(
            {
                "raw_data_id": raw.id,
                "enterprise_id": raw.enterprise_id,
                "file_name": raw.file_name,
                "upload_time": raw.upload_time.isoformat() if raw.upload_time else "",
                "parse_status": raw.parse_status,
                "parsed_count": parsed_count,
                "activity_count": activity_count,
                "is_completed": is_completed,
            }
        )

    total_count = len(raw_rows)
    completion_rate = round((completed_count / total_count * 100), 2) if total_count > 0 else 0.0

    return OCRChainOverviewResponse(
        success=True,
        total_count=total_count,
        completed_count=completed_count,
        completion_rate=completion_rate,
        records=records,
        message="链路总览生成完成",
    )
