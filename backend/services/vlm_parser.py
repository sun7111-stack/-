
import os
from fastapi import UploadFile

# 定义模拟模式的识别结果
MOCK_RESULTS = {
    'electricity_bill': {
        'doc_type': 'electricity_bill',
        'confidence': 0.95,
        'fields': {
            'amount': 1245,
            'unit': 'kWh',
            'period': '2025-03',
            'vendor': '国家电网'
        },
        'raw_text': '电费账单\n用电量: 1245 kWh\n计费期间: 2025-03\n开票单位: 国家电网',
        'suggested_activity_type': 'electricity'
    },
    'logistics_bill': {
        'doc_type': 'logistics_bill',
        'confidence': 0.92,
        'fields': {
            'distance': 350,
            'weight': 2.5,
            'transport_type': '陆运',
            'vendor': '顺丰速运'
        },
        'raw_text': '物流面单\n运单号: SF1234567890\n距离: 350 km\n重量: 2.5 kg\n承运方: 顺丰速运',
        'suggested_activity_type': 'air_logistics'
    },
    'fuel_bill': {
        'doc_type': 'fuel_bill',
        'confidence': 0.98,
        'fields': {
            'amount': 45.6,
            'unit': 'L',
            'period': '2025-03-15',
            'vendor': '中国石化'
        },
        'raw_text': '加油发票\n油品: 95#汽油\n加油量: 45.6 L\n金额: 386.52元\n供应商: 中国石化',
        'suggested_activity_type': 'diesel'
    }
}

async def parse_document_mock(file: UploadFile) -> dict:
    filename = (file.filename or '').lower()
    
    if '物流' in filename or '快递' in filename or 'logistics' in filename:
        return MOCK_RESULTS['logistics_bill']
    elif '油' in filename or 'fuel' in filename or '加油' in filename:
        return MOCK_RESULTS['fuel_bill']
    else:
        return MOCK_RESULTS['electricity_bill']

async def parse_document_with_llm(file: UploadFile) -> dict:
    return await parse_document_mock(file)

async def parse_document(file: UploadFile) -> dict:
    api_key = os.getenv('LLM_API_KEY')
    
    if api_key:
        return await parse_document_with_llm(file)
    else:
        return await parse_document_mock(file)

