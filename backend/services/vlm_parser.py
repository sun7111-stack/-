import os
import io
import json
import base64
import re
from typing import Dict, Any, BinaryIO, Optional, Tuple
from pypdf import PdfReader
from dotenv import load_dotenv

try:
    import dashscope
    from dashscope import MultiModalConversation

    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False

load_dotenv()


class OCRSettings:
    DASHSCOPE_API_KEY: Optional[str] = os.getenv("DASHSCOPE_API_KEY", None)
    DASHSCOPE_MODELS = [
        m.strip()
        for m in os.getenv("DASHSCOPE_MODELS", "qwen-vl-max,qwen-vl-plus").split(",")
        if m.strip()
    ]
    USE_MOCK: bool = not DASHSCOPE_API_KEY or not DASHSCOPE_AVAILABLE
    SUPPORTED_TYPES = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    MAX_SIZE = 10 * 1024 * 1024
    ACTIVITY_TYPES = {
        "electricity",
        "natural_gas",
        "diesel",
        "air_logistics",
        "warehouse_energy",
        "reverse_logistics",
        "packaging_waste",
        "waste",
    }


settings = OCRSettings()


class VLMParser:
    @staticmethod
    def _normalize_activity_type(value: Optional[str]) -> str:
        if value in settings.ACTIVITY_TYPES:
            return value
        return "waste"

    @staticmethod
    def _extract_json_text(raw: str) -> str:
        cleaned = raw.strip().replace("```json", "").replace("```", "")
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and start < end:
            return cleaned[start : end + 1]
        return cleaned

    @staticmethod
    def _read_file(file: BinaryIO, filename: str) -> tuple[bytes, str, str]:
        content = file.read()
        file.seek(0)
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            return content, filename.split(".")[-1], "image"
        if filename.lower().endswith(".pdf"):
            return content, "pdf", "pdf"
        raise ValueError("不支持 JPG/PNG/PDF 格式")

    @staticmethod
    def _detect_document_complexity(content: bytes, filename: str, mime_type: str) -> str:
        fn_lower = filename.lower()
        if any(x in fn_lower for x in ["发票", "invoice", "bill"]):
            complexity = "standard"
        elif any(x in fn_lower for x in ["复杂", "表格", "form", "excel"]):
            complexity = "complex"
        else:
            complexity = "simple"

        if mime_type == "pdf":
            try:
                reader = PdfReader(io.BytesIO(content))
                if len(reader.pages) > 2:
                    complexity = "complex"
                else:
                    text = "\n".join([p.extract_text() or "" for p in reader.pages])
                    if len(re.findall(r"[\|─┼┤├]", text)) > 10:
                        complexity = "complex"
            except Exception:
                pass

        return complexity

    @staticmethod
    def _simple_ocr_fallback(filename: str, raw_text: str = "") -> Tuple[Dict, float]:
        result = {
            "confidence": 0.5,
            "raw_text": raw_text,
            "doc_type": "unknown",
            "suggested_activity_type": "waste",
            "fields": {},
            "parse_method": "simple_heuristic",
        }

        combined = filename.lower() + " " + (raw_text.lower() if raw_text else "")

        if any(x in combined for x in ["电", "electricity", "kwh", "用电"]):
            result["doc_type"] = "electricity_bill"
            result["suggested_activity_type"] = "electricity"
            result["confidence"] = 0.75
            match = re.search(r"(\d+\.?\d*)\s*[kK][wW][hH]", raw_text or "")
            if match:
                result["fields"]["amount"] = float(match.group(1))
                result["fields"]["unit"] = "kWh"
                result["confidence"] = 0.85
        elif any(x in combined for x in ["运输", "logistics", "物流", "km", "公里"]):
            result["doc_type"] = "logistics_bill"
            result["suggested_activity_type"] = "air_logistics"
            result["confidence"] = 0.70
            match = re.search(r"(\d+\.?\d*)\s*[kK][mM]|(\d+\.?\d*)公里", raw_text or "")
            if match:
                dist = float(match.group(1) or match.group(2))
                result["fields"]["distance"] = dist
                result["fields"]["unit"] = "km"
                result["confidence"] = 0.80
        elif any(x in combined for x in ["油", "fuel", "汽油", "柴油"]):
            result["doc_type"] = "fuel_bill"
            result["suggested_activity_type"] = "diesel"
            result["confidence"] = 0.75
            match = re.search(r"(\d+\.?\d*)\s*[升L]", raw_text or "")
            if match:
                result["fields"]["amount"] = float(match.group(1))
                result["fields"]["unit"] = "L"
                result["confidence"] = 0.85

        return result, result["confidence"]

    @staticmethod
    def _parse_mock(filename: str, raw_text: str = "") -> Dict[str, Any]:
        fn_lower = filename.lower()
        result = {
            "confidence": 0.95,
            "raw_text": raw_text or "Mock模式原始文本",
            "doc_type": "unknown",
            "suggested_activity_type": "waste",
            "fields": {},
            "parse_method": "mock",
        }

        if "电" in fn_lower or "electricity" in fn_lower:
            result["doc_type"] = "electricity_bill"
            result["suggested_activity_type"] = "electricity"
            result["fields"] = {
                "amount": 1245,
                "unit": "kWh",
                "period": "2025-03",
                "vendor": "国家电网",
                "total_amount": 871.5,
                "price": 0.6999,
            }
        elif "运输" in fn_lower or "logistics" in fn_lower or "物流" in fn_lower:
            result["doc_type"] = "logistics_bill"
            result["suggested_activity_type"] = "air_logistics"
            result["fields"] = {
                "distance": 1200,
                "unit": "km",
                "weight": 2.5,
                "weight_unit": "t",
                "transport_type": "road",
                "vendor": "顺丰快递",
                "waybill_no": "SF1234567890",
            }
        elif "油" in fn_lower or "fuel" in fn_lower:
            result["doc_type"] = "fuel_bill"
            result["suggested_activity_type"] = "diesel"
            result["fields"] = {
                "amount": 300,
                "unit": "L",
                "period": "2025-03",
                "vendor": "中国石油",
                "fuel_type": "0#柴油",
                "total_amount": 2100,
            }
        else:
            result["confidence"] = 0.5
            result["message"] = "未能确定票据类别"

        return result

    @staticmethod
    def _parse_vlm_advanced(file_content: bytes, suffix: str, mime_type: str, complexity: str) -> Dict[str, Any]:
        if not DASHSCOPE_AVAILABLE:
            raise Exception("未安装dashscope SDK，请运行 pip install dashscope")
        if not settings.DASHSCOPE_API_KEY:
            raise Exception("未配置DASHSCOPE_API_KEY")

        dashscope.api_key = settings.DASHSCOPE_API_KEY

        system_prompt = f"""
        你是企业碳核算平台的票据识别专家。这份文档展现为'{complexity}'复杂度，需要精准识别。
        返回纯JSON格式，包含字段：doc_type, confidence, fields, raw_text, suggested_activity_type, complexity_notes。
        对复杂版式（多栏、表格、模糊截图），优先识别关键数值并标注低置信度区域。
        """

        if mime_type == "image":
            base64_str = base64.b64encode(file_content).decode("utf-8")
            messages = [{
                "role": "user",
                "content": [
                    {"image": f"data:image/{suffix};base64,{base64_str}"},
                    {"text": system_prompt},
                ],
            }]
        else:
            reader = PdfReader(io.BytesIO(file_content))
            text = "\n".join([p.extract_text() or "" for p in reader.pages])
            messages = [{
                "role": "user",
                "content": [{"text": f"{system_prompt}\n\n票据文本内容：\n{text}"}],
            }]

        model_errors = []
        for model_name in settings.DASHSCOPE_MODELS:
            try:
                response = MultiModalConversation.call(model=model_name, messages=messages)
                if response.status_code != 200:
                    model_errors.append(f"{model_name}: {response.code}")
                    continue

                output_text = response.output.choices[0].message.content[0]["text"]
                parsed = json.loads(VLMParser._extract_json_text(output_text))
                parsed["suggested_activity_type"] = VLMParser._normalize_activity_type(parsed.get("suggested_activity_type"))
                parsed["parse_method"] = f"vlm_advanced({model_name})"
                parsed["complexity"] = complexity
                return parsed
            except Exception as e:
                model_errors.append(f"{model_name}: {str(e)}")

        raise Exception(f"VLM API调用失败: {'; '.join(model_errors)}")

    @classmethod
    def parse_document(cls, file_obj: BinaryIO, filename: str) -> Dict[str, Any]:
        content, suffix, mime_type = cls._read_file(file_obj, filename)

        raw_text = ""
        if mime_type == "pdf":
            try:
                reader = PdfReader(io.BytesIO(content))
                raw_text = "\n".join([p.extract_text() or "" for p in reader.pages])
            except Exception:
                raw_text = ""

        complexity = cls._detect_document_complexity(content, filename, mime_type)

        if settings.USE_MOCK:
            mock_result = cls._parse_mock(filename, raw_text)
            mock_result["complexity"] = complexity
            return mock_result

        simple_result, simple_conf = cls._simple_ocr_fallback(filename, raw_text)
        simple_result["complexity"] = complexity

        if simple_conf >= 0.75 and complexity != "complex":
            return simple_result

        try:
            return cls._parse_vlm_advanced(content, suffix, mime_type, complexity)
        except Exception as vlm_error:
            simple_result["parse_warning"] = f"VLM降级失败: {str(vlm_error)}"
            simple_result["confidence"] = max(simple_conf, 0.4)
            return simple_result


async def parse_document_wrapper(file_obj) -> dict:
    return VLMParser.parse_document(file_obj.file, file_obj.filename)
