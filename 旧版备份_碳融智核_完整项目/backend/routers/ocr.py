"""OCR识别路由（模拟）"""
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="/api/ocr", tags=["OCR票据识别"])

# 模拟OCR识别结果（与前端script.js中的sampleResults一致）
SAMPLE_RESULTS = {
    "electricity": {
        "title": "电费单识别结果",
        "data": {
            "用电类型": "工商业用电",
            "用电量": "1,245 kWh",
            "电费金额": "¥ 1,245.00",
            "计费期间": "2024年3月1日-3月31日",
            "识别准确率": "98.5%",
        },
        "parsed": {
            "electricity_usage": 1245,
            "electricity_cost": 1245,
        },
    },
    "logistics": {
        "title": "物流面单识别结果",
        "data": {
            "运单号": "SF1234567890",
            "收件人": "张先生",
            "重量": "2.5 kg",
            "运输距离": "350 km",
            "运输方式": "陆运",
            "识别准确率": "96.2%",
        },
        "parsed": {
            "logistics_distance": 350,
            "logistics_weight": 2.5,
        },
    },
    "fuel": {
        "title": "加油发票识别结果",
        "data": {
            "油品类型": "95#汽油",
            "加油量": "45.6 L",
            "金额": "¥ 386.52",
            "加油站": "中国石化",
            "识别准确率": "97.8%",
        },
        "parsed": {
            "fuel_usage": 45.6,
            "fuel_cost": 386.52,
        },
    },
}

ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/jpg",
    "application/pdf",
}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/recognize", summary="上传票据进行OCR识别")
async def recognize(file: UploadFile = File(...)):
    """
    模拟OCR识别。
    实际场景中可接入百度OCR、腾讯OCR或自建识别服务。
    """
    # 验证文件类型
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="请上传图片文件 (JPEG, PNG) 或 PDF 文件")

    # 读取文件（验证大小）
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="文件太大，请上传小于10MB的文件")

    # 根据文件名猜测票据类型
    filename = (file.filename or "").lower()
    if "物流" in filename or "快递" in filename or "logistics" in filename:
        doc_type = "logistics"
    elif "油" in filename or "fuel" in filename or "加油" in filename:
        doc_type = "fuel"
    else:
        doc_type = "electricity"

    result = SAMPLE_RESULTS[doc_type]

    return {
        "success": True,
        "doc_type": doc_type,
        "title": result["title"],
        "data": result["data"],
        "parsed": result["parsed"],
    }


@router.get("/sample/{doc_type}", summary="获取示例识别结果")
def get_sample(doc_type: str):
    """获取指定类型的示例识别数据"""
    result = SAMPLE_RESULTS.get(doc_type)
    if not result:
        raise HTTPException(status_code=400, detail=f"不支持的文档类型: {doc_type}")
    return {
        "success": True,
        "doc_type": doc_type,
        "title": result["title"],
        "data": result["data"],
        "parsed": result["parsed"],
    }
