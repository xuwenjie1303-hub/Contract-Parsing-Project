import re 
from rapidfuzz import fuzz
from app.services.data import FIELD_ALIASES
#找到原文数据

#FOUND
#fuzz found
#NOT_FOUND
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
    best_match = []
    result=[]
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
            if not line.strip():
                search_start += len(line) + 1
                continue
            normalize_line = normalize_text(line)
            
            for factor in keywords:
                match_score = 0
                normalize_factor = normalize_text(factor)
          
                if normalize_factor in normalize_line:
                    match_score = 100
                    best_match.append ({
                    "page": page,
                    "line": line,
                    "score": match_score,
                })
                else:
                    if match_score < 100:
                        if len(normalize_factor)<len(normalize_line):
                            match_score = fuzz.partial_ratio(
                                normalize_factor,
                                normalize_line,
                            )
                    if match_score>fuzzy_threshold:
                        best_match.append ({
                                            "page": page,
                                            "line": line,
                                            "score": match_score,
                                        })


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

        return [{
            "status": "NOT_FOUND",
            "page": None,
            "text": None,
            "score": None,
        }]        

    for i,item in enumerate(best_match):
        page = item["page"]
        line = item["line"]
    
        index = page.text.find(line)
   
        start = max(0, index - context_chars)
        end = min(
            len(page.text),
            index + len(line) + context_chars,
        )
        source_text = page.text[start:end].strip()

        status = (
            "FOUND"
            if item["score"] == 100
            else "FUZZY_MATCH"
        )
        result.append({
        "status": status,
        "page": page.page_number,
        "text": source_text,
        "score": item["score"],
        })
    return result[0:10]

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

                    return [{
                        "status": "VALUE_MATCH",
                        "page": page.page_number,
                        "text": source_text,
                        "score": 100,
                    }]
    return None