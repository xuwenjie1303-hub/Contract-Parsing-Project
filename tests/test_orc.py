import pymupdf
from app.services.ocr_service import OCRService

pdf_path = "/Users/xuwenjie/Python/project_30_days/PDF_proj/data/2025-01s10扬州至淮南高速公路项目（合同）.pdf"

doc = pymupdf.open(pdf_path)
ocr = OCRService()

page = doc[0]
result = ocr.recognize_page(page)

print("识别文字：")
print(result["text"])

print("\n平均 OCR 分数：")
print(result["avg_confidence"])

print("\n识别区域数量：")
print(len(result["blocks"]))