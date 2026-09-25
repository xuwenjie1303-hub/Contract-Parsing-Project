import json
import re


def clean_llm_output(text: str) -> str:
    text = text.strip()

    # 去掉 markdown code fence
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    return text.strip()

def extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or start >= end:
        raise ValueError("未找到有效 JSON 对象")

    return text[start:end + 1]

def repair_json(text: str) -> str:
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)

    return text

def parse_llm_json(text: str) -> dict:
    cleaned = clean_llm_output(text)
    json_text = extract_json_object(cleaned)

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        repaired = repair_json(json_text)

        try:
            return json.loads(repaired)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM 返回内容无法解析为 JSON: {e}"
            ) from e