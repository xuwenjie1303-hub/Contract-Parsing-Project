import re 
from rapidfuzz import fuzz
import sys
from pathlib import Path
import json
proj_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(proj_root))
import logging
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
        "总金额",
        "交易总金额",
        "交易数字",
        "合同金额",
        "合同总额",
        "合同总价",
        "含税总价",
        "总金额",
    ],
    "货币单位":[
        "元",
        "英镑",
        "美元",
        "人民币",
    ],
    "签署日期":[
        "签署时间",
        "合同日期",
        "日期",
    ]


}
import re
import unicodedata

def normalize_text(text: str) -> str:
    # Unicode 规范化
    text = unicodedata.normalize("NFKC", text)

    # 小写
    text = text.lower()

    # 去除所有空白字符
    text = re.sub(r"\s+", "", text)

    # 去掉常见标点
    text = re.sub(
        r"[，。、“”‘’：；！？（）()【】\[\]:,.!?]",
        "",
        text,
    )

    return text

def get_keywords(keyword: str):
    return FIELD_ALIASES.get(keyword, [keyword])

# def find_evidence(document, keyword, value=None, context_chars=100, fuzzy_threshold=75):
#     keywords = get_keywords(keyword)
#     best_match = None
#     early_stop = False
#     search_start=0
#     for page_idx, page in enumerate(document.pages):
#         if early_stop:
#             print(f"[DEBUG] early_stop触发，退出页面循环")
#             break
#         page_text = page.text
#         if not page_text:
#             continue
#         lines = page.text.splitlines()

#         for i, line in enumerate(lines):
#             if early_stop:
#                 print(f"[DEBUG] early_stop触发，退出行循环")
#                 break
#             if not line.strip():
#                 continue

#             normalize_line = normalize_text(line)

#             for factor in keywords:
#                 match_score = 0
#                 normalize_factor = normalize_text(factor)

#                 # 精确匹配
#                 if normalize_factor in normalize_line:
#                     match_score = 100
#                 else:
#                     match_score = fuzz.partial_ratio(normalize_factor, normalize_line)

#                 if match_score < fuzzy_threshold:
#                     continue

#                 # 更新最优匹配
#                 if best_match is None or match_score > best_match["score"]:
#                     best_match = {
#                         "page": page,
#                         "line": line,
#                         "score": match_score,
#                     }
#                     # ✅只要更新匹配，立刻打印！不要放在if精确里面
#                     print(f"✅找到匹配 | score={match_score}, factor={factor}")
#                     print(f"    line_content: {line}")

#                     if best_match["score"] == 100:
#                         print(f"💯拿到满分100，准备开启early_stop")
#                         early_stop = True
#                         break   # 跳出 for factor in keywords
#             search_start += len(line) +1
#     if best_match is None:
#         if value is not None:
#             evidence = search_by_value(
#                 document,
#                 value,
#                 context_chars,
#             )

#         if evidence is not None:
#             return evidence

#         return {
#             "status": "NOT_FOUND",
#             "page": None,
#             "text": None,
#             "score": None,
#         }        
#     page = best_match["page"]
#     line = best_match["line"]
    
#     index = page.text.find(line)
#     if index == -1:
#         return {
#             "status": "NOT_FOUND",
#             "page": None,
#             "text": None,
#             "score": None,
#         }        
#     start = max(0, index - context_chars)
#     end = min(
#         len(page.text),
#         index + len(line) + context_chars,
#     )
#     source_text = page.text[start:end].strip()

#     status = (
#         "FOUND"
#         if best_match["score"] == 100
#         else "FUZZY_MATCH"
#     )

#     return {
#         "status": status,
#         "page": page.page_number,
#         "text": source_text,
#         "score": best_match["score"],
#     }


def find_evidence(document, keyword, value=None, context_chars=100, fuzzy_threshold=75):
    keywords = get_keywords(keyword)
    best_match = None
    early_stop = False
    for page in document.pages:
        if early_stop:
            break
        page_text = page.text

        if not page_text:
            continue
        lines = page.text.splitlines()
        search_start = 0
        for i, line in enumerate(lines):
            if early_stop:
                break
            if not line.strip():
                search_start += len(line) + 1
                continue
            normalize_line = normalize_text(line)
            
            for factor in keywords:
                match_score = 0
                normalize_factor = normalize_text(factor)
                # print(normalize_factor)
                # print(normalize_line)
          
                if normalize_factor in normalize_line:
                    match_score = 100
                    print(normalize_factor)
                    print(normalize_line)

                else:
                    if match_score < 100:
                        if len(normalize_factor)<len(normalize_line):
                            match_score = fuzz.partial_ratio(
                                normalize_factor,
                                normalize_line,
                            )
                    if match_score>90:
                        print(match_score)
                        print(normalize_line)
                        print(normalize_factor)
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
                    if best_match["score"] == 100:
                        early_stop = True
                        break
            search_start += len(line) + 1
    if best_match is None:
        if value is not None:
            evidence = search_by_value(
                document,
                value,
                context_chars,
            )

        if evidence is not None:
            return evidence

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

def search_by_value(document, value, context_chars=100):

    if value is None:
        return None

    value_str = str(value)

    # 例如 12800 → ["12800", "12,800", "12800.0", "12800.00"]
    candidates = [
        value_str,
        value_str.replace(",", ""),
    ]

    for page in document.pages:
        page_text = page.text

        if not page_text:
            continue
        
        lines = page.text.splitlines()
        normalized_page = normalize_text(page_text)
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            normalize_line=normalize_text(line)
            for candidate in candidates:
                normalized_candidate = normalize_text(candidate)

                if normalized_candidate in normalize_line:
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)

                    source_text = "\n".join(lines[start:end])

                    return {
                        "status": "VALUE_MATCH",
                        "page": page.page_number,
                        "text": source_text,
                        "score": 100,
                    }
    return None

result = extract_text_from_pdf("/Users/xuwenjie/Python/project_30_days/PDF_proj/data/桃溪示范园中水回用设备采购合同.pdf")
for fname in Contract.model_fields.keys():
    if fname == "amount_value":
        evidence = find_evidence(result, Contract.model_fields[fname].description)
print(evidence["text"])
# print(evidence)