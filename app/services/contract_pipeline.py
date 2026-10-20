import logging

from app.parsers.pdf_parsers import extract_text_from_pdf
from app.services.llm_service import call_llm
from app.services.normalizer import normalize_amount, normalize_date
from app.services.validator import check_output
from app.services.json_parser import parse_llm_json
from app.services.retriever import ContractRetriever
from app.model.contract import (
    ContractLLMOutput,
    build_contract,
    supply_system,
)
from app.model.document import product_texts
from app.services.retriever import build_rag_prompt

logger = logging.getLogger(__name__)


def process_contract(pdf_bytes: bytes, filename: str):
    """处理单份合同，成功时返回结构化合同对象。"""

    # 1. 解析 PDF
    document_result = extract_text_from_pdf(pdf_bytes, filename)

    # # 2. 提取文本
    # text_parts = product_texts(document_result)

    # # TODO: 后续替换为完整的分块策略，
    # # 不要直接静默丢弃第五个片段之后的内容。
    # document_text = " ".join(text_parts)

    # # 3. 构造 Prompt
    # schema = ContractLLMOutput.model_json_schema()

    # prompt = f"""
    # #                 你是一个企业合同信息抽取助手。请根据提供的合同文本提取以下信息:
    # #                 {schema}
    # #                 只返回结构化结果，不要添加额外解释。       
    # #                 1. 输出JSON**严格只包含下面列出的key，禁止增加任何额外字段、注释、解释文字**。
    # #                 2. amount_value：提取合同内的**合同总金额**；如果是按月租赁，提取整个合同周期总租金；
    # #                 3. 如果找不到对应值，返回null，不要编造内容。
    # #                 4. 不要输出markdown```json标记，直接输出纯JSON。
     
    # #                 合同文本为：
    # #                 {document_text}
    # #                 """
    prompt = build_rag_prompt(document_result, ContractRetriever())[0]
    evidence_text = build_rag_prompt(document_result, ContractRetriever())[1]
    # 4. 调用 LLM
    raw_output = call_llm(prompt)
    # 5. 解析 JSON
    raw_data = parse_llm_json (raw_output)
  
    inner_dict = raw_data.get ("properties", raw_data)
    print(inner_dict)
    llm_result = ContractLLMOutput (**inner_dict)
    # 请根据 parse_llm_json 的实际返回格式调整这里。
    # TODO: 想这里该怎么处理json格式错乱，回应不正常的问题
    # 如果返回的是业务数据字典，直接校验即可。
  
    # 6. 转换为业务对象
    contract = build_contract(llm_result)

    # 7. 建立原文溯源
    supply_system(evidence_text, contract)

    # 8. 归一化
    contract.amount_value.value = normalize_amount(
        contract.amount_value.value
    )
    contract.sign_date.value = normalize_date(
        contract.sign_date.value
    )

    # 9. 业务校验
    check_output(contract)

    return contract
