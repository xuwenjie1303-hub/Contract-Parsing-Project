
import os
from openai import OpenAI
# 加载项目根目录下的.env文件



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

if __name__ == "__main__":
    # 本地测试入口，直接运行这个py文件测试连通性
    document="合同编号：123456 甲方：ABC有限公司. 乙方：DEF公司 合同金额：人民币壹佰贰拾伍万元整 签署日期：2023年5月1日"
    test_prompt = f"""
                你是一个企业合同信息抽取助手。请根据提供的合同文本提取以下信息:
                1. contract_number:合同编号
                2. party_a:甲方
                3. party_b:乙方
                4. amount:合同金额
                5. sign_date:签署日期
                只返回结构化结果，不要添加额外解释。

                合同文本为：
                {document}
                """
    output = call_llm(test_prompt)
    print("模型输出:\n", output)