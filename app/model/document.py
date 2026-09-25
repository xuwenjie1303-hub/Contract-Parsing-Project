import pymupdf as fitz
from dataclasses import dataclass


@dataclass
class PageText:
    page_number: int
    text: str

@dataclass
class Document:
    filename:str
    pages_count:int
    pages:list[PageText]

def product_texts(result):
    ls=[]
    for i in range(result.pages_count):
        ls.append(result.pages[i].text)
    return ls