from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from services.vlm_parser import parse_document_wrapper, settings

router = APIRouter(prefix='/api/ocr', tags=['OCR票据识别'])

# ================== 数据模型 (Schemas) ==================
class OCRParseResult(BaseModel):
    doc_type: str = Field(..., description="票据类型枚举")
    confidence: float = Field(..., ge=0, le=1, description="识别置信度")
    fields: Dict[str, Any] = Field(..., description="结构化关键字段")
    raw_text: str = Field(..., description="原始文本(存证用)")
    suggested_activity_type: str = Field(..., description="碳核算活动类型")
    message: Optional[str] = None

class OCRResponse(BaseModel):
    success: bool
    data: Optional[OCRParseResult] = None
    message: str = ""

@router.get('/health', summary='健康检查与模式探测')
async def health_check():
    return {
        "status": "ok",
        "mock_mode": settings.USE_MOCK,
        "message": "碳融智核OCR服务运行正常"
    }

@router.post('/recognize', response_model=OCRResponse, summary='票据结构化识别')
async def recognize(file: UploadFile = File(...)):
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
        result_data = await parse_document_wrapper(file)
        return OCRResponse(
            success=True,
            data=OCRParseResult(**result_data),
            message="识别成功"
        )
    except Exception as e:
        return OCRResponse(
            success=False,
            message=f"识别失败: {str(e)}"
        )
