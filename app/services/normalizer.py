import re
from datetime import datetime

def normalize_amount(value: str | float | int) -> float:
    if isinstance(value, (int, float)):
        return float(value)

    value = value.replace(",", "")
    value = value.replace("¥", "")
    value = value.replace("元", "")
    value = value.replace("英镑", "")
    value = value.strip()

    if value.endswith("万"):
        value = value[:-1]
        return float(value) * 10000
    # if value == None:
    #     return None
    return float(value)


def normalize_date(date_text: str | None) -> str | None:
    """
    将杂乱日期字符串归一化为 YYYY‑MM‑DD
    解析失败返回 None
    """
    if not date_text:
        return None
    date_text = date_text.strip()
    clean_text = date_text.replace("\xa0", " ").replace("\n", "").replace("\r", "").strip()
    clean_text = re.sub(r"\s*([年月日])\s*", r"\1", clean_text)
    # 在这里扩充你PDF里面可能出现的全部日期格式
    formats = [
        "%Y‑%m‑%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y年%m月%d日",
        "%d‑%m‑%Y",
        "%b %d, %Y",   # Aug 28, 2026
        "%Y 年 %m 月 %d 日",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(clean_text, fmt)
            return dt.strftime("%Y‑%m‑%d")
        except ValueError:
            continue
    # 所有格式都解析失败
    return None