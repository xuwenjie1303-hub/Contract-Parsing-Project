import pymupdf as fitz
from dataclasses import dataclass
from app.model.document import PageText,Document


def extract_text_from_pdf(pdf_input: str, filename: str|None = None) -> dataclass:
    if isinstance(pdf_input,str):
        try:
            doc = fitz.open(pdf_input)
        except Exception as e:
            print(f"Failed to open PDF: {e}")
    if isinstance(pdf_input,bytes):
        try:
            doc = fitz.open('pdf',pdf_input)
        except Exception as e:
            print(f"Failed to open PDF: {e}")
    pages=[]
    for i,page in enumerate(doc):
        pages.append(
            PageText(
                page_number=i+1,
                text=page.get_text(sort=True)
            )
        )
    result = Document(
        filename=filename,
        pages_count=len(doc),
        pages=pages
    )
  
    doc.close()

    return result
