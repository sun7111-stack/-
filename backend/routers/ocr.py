
from fastapi import APIRouter, UploadFile, File, HTTPException
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.vlm_parser import parse_document

router = APIRouter(prefix='/api/ocr', tags=['OCR票据识别'])

ALLOWED_TYPES = {'image/jpeg', 'image/png', 'image/jpg', 'application/pdf'}

@router.post('/recognize', summary='上传票据进行OCR识别')
async def recognize(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        return {'success': False, 'message': '请上传图片或PDF文件'}
    
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        return {'success': False, 'message': '文件太大'}
        
    await file.seek(0)
    
    try:
        result = await parse_document(file)
        return {
            'success': True,
            'data': result
        }
    except Exception as e:
        return {
            'success': False,
            'message': '无法识别该票据，请更换更清晰的图片'
        }

