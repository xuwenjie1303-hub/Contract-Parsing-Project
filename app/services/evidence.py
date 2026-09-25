import re 
from rapidfuzz import fuzz

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
        "总金额",
        "交易总金额",
        "交易数字",
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

def find_evidence(document, keyword, value=None, context_chars=100, fuzzy_threshold=75):
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
                if normalize_factor in normalize_line:
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