import os
from openai import OpenAI


def call_llm(prompt: str, model: str = "qwen2:7b") -> str:
    """
    调用本地Ollama大模型
    :param prompt: 传给大模型的提示词（可以是PDF文本+指令）
    :param model: ollama模型名称
    :return: 返回模型输出文本
    """
    client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="dummy_ollama_key"
)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,   # 做文档解析，温度调低，输出更稳定、少幻觉
    )
    result = resp.choices[0].message.content
    return result