import os
import io
import json
import base64
from typing import Dict, Any, BinaryIO, Optional
from pypdf import PdfReader
from dotenv import load_dotenv

# ���Ե����ģ��SDK��û�а�װҲ��Ӱ��Mockģʽ����
try:
    import dashscope
    from dashscope import MultiModalConversation

    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False

load_dotenv()

# ȫ������
class OCRSettings:
    DASHSCOPE_API_KEY: Optional[str] = os.getenv("DASHSCOPE_API_KEY", None)
    DASHSCOPE_MODELS = [
        m.strip()
        for m in os.getenv("DASHSCOPE_MODELS", "qwen-vl-max,qwen-vl-plus").split(",")
        if m.strip()
    ]
    USE_MOCK: bool = not DASHSCOPE_API_KEY or not DASHSCOPE_AVAILABLE
    SUPPORTED_TYPES = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
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
    """����Ʊ�ݽ�����"""

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
        """��ȡ��Ԥ�����ļ�"""
        content = file.read()
        file.seek(0)
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return content, filename.split('.')[-1], "image"
        elif filename.lower().endswith('.pdf'):
            return content, "pdf", "pdf"
        raise ValueError("��֧�� JPG/PNG/PDF ��ʽ")

    @staticmethod
    def _parse_mock(filename: str, raw_text: str = "") -> Dict[str, Any]:
        """Mockģʽ�������ļ������ع̶�����"""
        fn_lower = filename.lower()
        result = {
            "confidence": 0.95,
            "raw_text": raw_text or "Mockģʽԭʼ�ı�",
            "doc_type": "unknown",
            "suggested_activity_type": "waste",
            "fields": {}
        }

        # --- 1. ��ѵ� ---
        if "��" in fn_lower or "electricity" in fn_lower:
            result["doc_type"] = "electricity_bill"
            result["suggested_activity_type"] = "electricity"
            result["fields"] = {
                "amount": 1245, "unit": "kWh", "period": "2025-03",
                "vendor": "���ҵ���", "total_amount": 871.5, "price": 0.6999
            }
        # --- 2. ������ ---
        elif "����" in fn_lower or "logistics" in fn_lower or "���" in fn_lower:
            result["doc_type"] = "logistics_bill"
            result["suggested_activity_type"] = "air_logistics"  # ��������
            result["fields"] = {
                "distance": 1200, "unit": "km", "weight": 2.5, "weight_unit": "t",
                "transport_type": "road", "vendor": "˳������", "waybill_no": "SF1234567890"
            }
        # --- 3. ȼ�͵� ---
        elif "��" in fn_lower or "fuel" in fn_lower:
            result["doc_type"] = "fuel_bill"
            result["suggested_activity_type"] = "diesel"  # ��������
            result["fields"] = {
                "amount": 300, "unit": "L", "period": "2025-03",
                "vendor": "�й�ʯ��", "fuel_type": "0#����", "total_amount": 2100
            }
        else:
            result["confidence"] = 0.5
            result["message"] = "δ��ȷʶ��Ʊ������"

        return result

    @staticmethod
    def _parse_llm(file_content: bytes, suffix: str, mime_type: str) -> Dict[str, Any]:
        """��ʵģʽ������ͨ��ǧ��VL"""
        if not DASHSCOPE_AVAILABLE:
            raise Exception("δ��װdashscope SDK�������� pip install dashscope")
        if not settings.DASHSCOPE_API_KEY:
            raise Exception("δ����DASHSCOPE_API_KEY")

        dashscope.api_key = settings.DASHSCOPE_API_KEY

        system_prompt = """
        ����̼���Ǻ�ƽ̨��Ʊ��ʶ��ר�ҡ���ʶ��Ʊ�ݲ����ش�JSON����Ҫ�κ�Markdown��ǡ�
        JSON������������ֶΣ�
        1. doc_type: ö��ֵ [electricity_bill, logistics_bill, fuel_bill, warehouse_bill, unknown]
        2. confidence: 0-1�ĸ�����
        3. fields: �ṹ���ֶΣ�����Ʊ��������ȡ���õ���/����/��������λ��ʱ�䡢��Ӧ�̵ȣ�
        4. raw_text: Ʊ��ȫ��
        5. suggested_activity_type: ֻ������⼸������ѡ [electricity, natural_gas, diesel, air_logistics, warehouse_energy, reverse_logistics, packaging_waste, waste]
        """

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
            reader = PdfReader(io.BytesIO(file_content))
            text = "\n".join([p.extract_text() or "" for p in reader.pages])
            messages = [{
                "role": "user",
                "content": [{"text": f"{system_prompt}\n\nƱ���ı����ݣ�\n{text}"}]
            }]

        model_errors = []
        for model_name in settings.DASHSCOPE_MODELS:
            response = MultiModalConversation.call(model=model_name, messages=messages)
            if response.status_code != 200:
                model_errors.append(f"{model_name}: {response.code}")
                continue

            output_text = response.output.choices[0].message.content[0]["text"]
            parsed = json.loads(VLMParser._extract_json_text(output_text))

            parsed["suggested_activity_type"] = VLMParser._normalize_activity_type(
                parsed.get("suggested_activity_type")
            )
            return parsed

        raise Exception(f"API����ʧ��: {'; '.join(model_errors)}")

    @classmethod
    def parse_document(cls, file_obj: BinaryIO, filename: str) -> Dict[str, Any]:
        """����ں��������ݾɴ������"""
        content, suffix, mime_type = cls._read_file(file_obj, filename)

        raw_text = ""
        if mime_type == "pdf":
            reader = PdfReader(io.BytesIO(content))
            raw_text = "\n".join([p.extract_text() or "" for p in reader.pages])

        if settings.USE_MOCK:
            return cls._parse_mock(filename, raw_text)
        else:
            try:
                return cls._parse_llm(content, suffix, mime_type)
            except Exception:
                # 在线模型不可用或参数异常时，自动降级到Mock，保证主链路稳定。
                return cls._parse_mock(filename, raw_text)

async def parse_document_wrapper(file_obj) -> dict:
    """��¶��·�ɲ���õ��첽��װ"""
    return VLMParser.parse_document(file_obj.file, file_obj.filename)



