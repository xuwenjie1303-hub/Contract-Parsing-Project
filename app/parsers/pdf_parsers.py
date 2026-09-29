import pymupdf as fitz
from dataclasses import dataclass
from app.model.document import PageText,Document
from app.services.ocr_service import OCRService

orc_service = OCRService()
def extract_text_from_pdf(pdf_input: str, filename: str|None = None,) -> dataclass:


    if isinstance(pdf_input,str):
        try:
            doc = fitz.open(pdf_input)
        except Exception as e:
            print(f"Failed to open PDF: {e}")
    elif isinstance(pdf_input,bytes):
        try:
            doc = fitz.open('pdf',pdf_input)
        except Exception as e:
            print(f"Failed to open PDF: {e}")

    if doc is None:
        raise RuntimeError("无法打开PDF文件")
    pages=[]
    for i,page in enumerate(doc):
        raw_text = page.get_text(sort=True)
        # strip() 把换行空格全部去掉，判断是否真正空页面
        if raw_text.strip() == "":
            # 需要OCR
            orc_result = orc_service.recognize_page(page)
            page_text = orc_result["text"]
        else:
            page_text = raw_text
        pages.append(
            PageText(
                page_number=i+1,
                text=page_text
            )
        )
        # print(page_text)
    result = Document(
        filename=filename,
        pages_count=len(doc),
        pages=pages
    )
  
    doc.close()

    return result
