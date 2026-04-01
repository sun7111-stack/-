import os
import io
import json
import base64
from typing import Dict, Any, Optional, BinaryIO
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image
from PyPDF2 import PdfReader

# 尝试导入大模型SDK，没有安装也不影响Mock模式运行
try:
    import dashscope
    from dashscope import MultiModalConversation

    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False

# ================== 配置与初始化 ==================
load_dotenv()
app = FastAPI(
    title="碳融智核-票据OCR结构化识别API",
    description="基于多模态AI的供应链碳会计平台 | 支持Mock/真实双模式",
    version="1.0.0"
)

# 配置CORS（允许前后端联调）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局配置
class Settings:
    DASHSCOPE_API_KEY: str | None = os.getenv("DASHSCOPE_API_KEY", None)
    USE_MOCK: bool = not DASHSCOPE_API_KEY or not DASHSCOPE_AVAILABLE
    SUPPORTED_TYPES = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    MAX_SIZE = 10 * 1024 * 1024  # 10MB

    # 票据类型与碳核算活动映射
    DOC_TYPE_MAP = {
        "electricity_bill": ("电费单", "electricity"),
        "logistics_bill": ("物流单", "transportation"),
        "fuel_bill": ("燃油单", "fuel_combustion"),
        "warehouse_bill": ("仓储单", "warehousing")
    }


settings = Settings()


# ================== 数据模型 (Schemas) ==================
class OCRParseResult(BaseModel):
    doc_type: str = Field(..., description="票据类型枚举")
    confidence: float = Field(..., ge=0, le=1, description="识别置信度")
    fields: Dict[str, Any] = Field(..., description="结构化关键字段")
    raw_text: str = Field(..., description="原始文本(存证用)")
    suggested_activity_type: str = Field(..., description="碳核算活动类型")


class OCRResponse(BaseModel):
    success: bool
    data: Optional[OCRParseResult] = None
    message: str = ""


# ================== 核心业务逻辑 (Services) ==================
class VLMParser:
    """核心票据解析器"""

    @staticmethod
    def _read_file(file: BinaryIO, filename: str) -> tuple[bytes, str, str]:
        """读取并预处理文件"""
        content = file.read()
        file.seek(0)
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return content, filename.split('.')[-1], "image"
        elif filename.lower().endswith('.pdf'):
            return content, "pdf", "pdf"
        raise ValueError("仅支持 JPG/PNG/PDF 格式")

    @staticmethod
    def _parse_mock(filename: str, raw_text: str = "") -> Dict[str, Any]:
        """Mock模式：根据文件名返回固定数据"""
        fn_lower = filename.lower()
        result = {
            "confidence": 0.95,
            "raw_text": raw_text or "Mock模式原始文本",
            "doc_type": "unknown",
            "suggested_activity_type": "unknown",
            "fields": {}
        }

        # --- 1. 电费单 ---
        if "电" in fn_lower or "electricity" in fn_lower:
            result["doc_type"] = "electricity_bill"
            result["suggested_activity_type"] = "electricity"
            result["fields"] = {
                "amount": 1245, "unit": "kWh", "period": "2025-03",
                "vendor": "国家电网", "total_amount": 871.5, "price": 0.6999
            }
        # --- 2. 物流单 ---
        elif "物流" in fn_lower or "logistics" in fn_lower or "快递" in fn_lower:
            result["doc_type"] = "logistics_bill"
            result["suggested_activity_type"] = "transportation"
            result["fields"] = {
                "distance": 1200, "unit": "km", "weight": 2.5, "weight_unit": "t",
                "transport_type": "road", "vendor": "顺丰速运", "waybill_no": "SF1234567890"
            }
        # --- 3. 燃油单 ---
        elif "油" in fn_lower or "fuel" in fn_lower:
            result["doc_type"] = "fuel_bill"
            result["suggested_activity_type"] = "fuel_combustion"
            result["fields"] = {
                "amount": 300, "unit": "L", "period": "2025-03",
                "vendor": "中国石油", "fuel_type": "0#柴油", "total_amount": 2100
            }
        else:
            result["confidence"] = 0.5
            result["message"] = "未明确识别到票据类型"

        return result

    @staticmethod
    def _parse_llm(file_content: bytes, suffix: str, mime_type: str) -> Dict[str, Any]:
        """真实模式：调用通义千问VL"""
        if not DASHSCOPE_AVAILABLE:
            raise Exception("未安装 dashscope SDK，请运行 pip install dashscope")
        if not settings.DASHSCOPE_API_KEY:
            raise Exception("未配置 DASHSCOPE_API_KEY")

        dashscope.api_key = settings.DASHSCOPE_API_KEY

        # 构建Prompt
        system_prompt = """
        你是碳融智核平台的票据识别专家。请识别票据并返回纯JSON，不要任何Markdown标记。
        JSON必须包含以下字段：
        1. doc_type: 枚举值 [electricity_bill, logistics_bill, fuel_bill, warehouse_bill, unknown]
        2. confidence: 0-1的浮点数
        3. fields: 结构化字段（根据票据类型提取：用电量/距离/油量、单位、时间、供应商等）
        4. raw_text: 票据全文
        5. suggested_activity_type: 枚举值 [electricity, transportation, fuel_combustion, warehousing, unknown]
        """

        # 准备输入
        if mime_type == "image":
            base64_str = base64.b64encode(file_content).decode('utf-8')
            messages = [{
                "role": "user",
                "content": [
                    {"image": f"data:image/{suffix};base64,{base64_str}"},
                    {"text": system_prompt}
                ]
            }]
        else:
            # PDF提取文本
            reader = PdfReader(io.BytesIO(file_content))
            text = "\n".join([p.extract_text() or "" for p in reader.pages])
            messages = [{
                "role": "user",
                "content": [{"text": f"{system_prompt}\n\n票据文本内容：\n{text}"}]
            }]

        # 调用API
        response = MultiModalConversation.call(model='qwen-vl-max', messages=messages)
        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.code}")

        # 解析结果
        output_text = response.output.choices[0].message.content[0]["text"]
        output_text = output_text.strip().replace("```json", "").replace("```", "")
        return json.loads(output_text)

    @classmethod
    def parse(cls, file: BinaryIO, filename: str) -> Dict[str, Any]:
        """主入口函数"""
        content, suffix, mime_type = cls._read_file(file, filename)

        # 获取Raw Text用于Mock
        raw_text = ""
        if mime_type == "pdf":
            reader = PdfReader(io.BytesIO(content))
            raw_text = "\n".join([p.extract_text() or "" for p in reader.pages])

        if settings.USE_MOCK:
            return cls._parse_mock(filename, raw_text)
        else:
            return cls._parse_llm(content, suffix, mime_type)


# ================== 路由层 (Routers) ==================
@app.get("/api/health", summary="健康检查")
async def health_check():
    return {
        "status": "ok",
        "mock_mode": settings.USE_MOCK,
        "message": "碳融智核OCR服务运行正常"
    }


@app.post("/api/ocr/recognize", response_model=OCRResponse, summary="票据结构化识别")
async def recognize(file: UploadFile = File(...)):
    # 1. 校验
    if file.content_type not in settings.SUPPORTED_TYPES:
        raise HTTPException(status_code=400, detail="文件格式不支持")

    # 读取一次检查大小
    content = await file.read()
    if len(content) > settings.MAX_SIZE:
        raise HTTPException(status_code=400, detail="文件过大")
    await file.seek(0)  # 重置指针

    # 2. 调用业务逻辑
    try:
        result_data = VLMParser.parse(file.file, file.filename)
        return OCRResponse(
            success=True,
            data=OCRParseResult(**result_data),
            message="识别成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================== 启动入口 ==================
if __name__ == "__main__":
    import uvicorn

    print(f"🚀 启动服务... Mock模式: {settings.USE_MOCK}")
    uvicorn.run(app, host="0.0.0.0", port=8000)