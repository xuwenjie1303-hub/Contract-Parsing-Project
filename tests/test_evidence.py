import re 
from rapidfuzz import fuzz
import sys
from pathlib import Path
import json
proj_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(proj_root))

import streamlit as st
from app.parsers.pdf_parsers import extract_text_from_pdf 
from app.services.llm_service import call_llm
from app.model.contract import ContractLLMOutput,Contract
from app.model.document import product_texts
from app.model.contract import supply_system,build_contract
from app.services.normalizer import normalize_amount,normalize_date
from app.services.validator import check_output
from app.services.json_parser import parse_llm_json
#找到原文数据

#FOUND
#fuzz found
#NOT_FOUND
FIELD_ALIASES = {
    "合同金额": [
        "合同金额",
        "合同总额",
        "合同总价",
        "含税总价",
        "总金额",
    ],

    "合同编号": [
        "合同编号",
        "合同号",
        "协议编号",
        "协议号",
    ],

    "主体A": [
        "甲方",
        "买方",
        "采购方",
        "委托方",
        
    ],

    "主体B": [
        "乙方",
        "卖方",
        "供应方",
        "受托方",
        
    ],
    "交易金额":[
        "总金额"
        "交易总金额"
        "交易数字"
    ],
    "货币单位":[
        "元"
        "英镑"
        "美元"
    ],
    "签署日期":[
        "签署时间"
        "合同日期"
        "日期"
    ]


}
def normalize_text(text: str) -> str:
    text = text.lower()

    # 删除空白和换行
    text = re.sub(r"\s+", "", text)

    # 删除常见标点
    text = re.sub(
        r"[，。、“”‘’：；！？（）()【】\[\]:,.!?]",
        "",
        text,
    )

    return text

def get_keywords(keyword: str):
    return FIELD_ALIASES.get(keyword, [keyword])

def find_evidence(document, keyword, context_chars=100, fuzzy_threshold=75):
    keywords = get_keywords(keyword)
    best_match = None
    for page in document.pages:
        page_text = page.text

        if not page_text:
            continue
        lines = page.text.splitlines()
        search_start = 0
        for i, line in enumerate(lines):
            if not line.strip():
                search_start += len(line) + 1
                continue
            normalize_line = normalize_text(line)
            for factor in keywords:
                normalize_factor = normalize_text(factor)
                if factor in line:
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)

                    source_text = "\n".join(lines[start:end])
                    match_score = 100
                    
                else:
                    match_score = fuzz.partial_ratio(
                        normalize_factor,
                        normalize_line,
                    )
                if match_score < fuzzy_threshold:
                    continue

                if (
                    best_match is None
                    or match_score > best_match["score"]
                ):
                    best_match = {
                        "page": page,
                        "line": line,
                        "score": match_score,
                    }

            search_start += len(line) + 1
    if best_match is None:
        return {
            "status": "NOT_FOUND",
            "page": None,
            "text": None,
            "score": None,
        }        
    page = best_match["page"]
    line = best_match["line"]
    index = page.text.find(line)
    if index == -1:
        return {
            "status": "NOT_FOUND",
            "page": None,
            "text": None,
            "score": None,
        }        
    start = max(0, index - context_chars)
    end = min(
        len(page.text),
        index + len(line) + context_chars,
    )
    source_text = page.text[start:end].strip()

    status = (
        "FOUND"
        if best_match["score"] == 100
        else "FUZZY_MATCH"
    )

    return {
        "status": status,
        "page": page.page_number,
        "text": source_text,
        "score": best_match["score"],
    }