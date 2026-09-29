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

def LLM_service(pdf_input,choice:int):
            try:
                result = extract_text_from_pdf(pdf_input)
            except Exception as e:
                logging.exception("处理文件失败")
                st.write("处理文件失败")

            text=' '
            ls=product_texts(result)
            document = text.join(ls[0:5])
            
            schema = ContractLLMOutput.model_json_schema()
            test_prompt = f"""
    #                 你是一个企业合同信息抽取助手。请根据提供的合同文本提取以下信息:
    #                 {schema}
    #                 只返回结构化结果，不要添加额外解释。      
    #                 1. 输出JSON**严格只包含下面列出的key，禁止增加任何额外字段、注释、解释文字**。
    #                 2. amount_value：提取合同内的**合同总金额**；如果是按月租赁，提取整个合同周期总租金；
    #                 3. 如果找不到对应值，返回null，不要编造内容。
    #                 4. 不要输出markdown```json标记，直接输出纯JSON。

    #                 合同文本为：
    #                 {document}
    #                 """
            try:
                st.write("🤖正在调用本地 LLM...")
                output = call_llm(test_prompt)
                st.write(output)
                st.write("✅完成")
            except Exception as e:
                logging.exception("模型处理出现错误")
                st.write("模型处理出现错误")
            try:
                raw_dict = parse_llm_json(output)
            # st.write(raw_dict)
            except Exception as e:
                logging.exception("模型输出json失败")
                st.write("模型输出json失败")

            # st.write(raw_dict)
            inner_dict = raw_dict.get("properties", raw_dict)
            llm_outputcontract = ContractLLMOutput(**inner_dict)
            # llm_outputcontract = ContractLLMOutput(**raw_dict)
            contractoutput = build_contract(llm_outputcontract)
        
            # print(f"LLM输出结果：{contractoutput.model_dump_json()}")
            # print(f"PDF前3000字符原文：{document[:3000]}")
            supply_system(result,contractoutput)
            print(contractoutput)
            l1 = normalize_amount(contractoutput.amount_value.value)
            l2 = normalize_date(contractoutput.sign_date.value)
            contractoutput.sign_date.value=l2
            contractoutput.amount_value.value=l1
            if choice ==0:
                return inner_dict
            else:
                return contractoutput