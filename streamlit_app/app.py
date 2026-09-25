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


logging.basicConfig(
    filename="app.log",
    # filemode="w",   # ✨每次启动覆盖，清空旧日志
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)



st.title("PDF信息提取系统")

# 三个能力卡片
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### ⚡ Local Inference")
    st.caption(
        "Powered by Ollama and Qwen2-7B. "
        "Document processing stays on your machine."
    )

with col2:
    st.markdown("### 🧩 Structured Output")
    st.caption(
        "Convert unstructured PDF content into "
        "validated structured fields."
    )

with col3:
    st.markdown("### 🔎 Evidence Traceability")
    st.caption(
        "Every extracted field can be traced "
        "back to its source page and text."
    )
st.markdown("### Upload a document")

uploaded_file=st.file_uploader(
    "upload PDF",
    type=['pdf']
)

st.caption(
    "Upload a PDF above to start extracting structured information."
)

if uploaded_file:
    st.write(uploaded_file.name)
    if st.button('读取'):
        with st.status("任务开始", expanded=True) as status:
            pdf_input = uploaded_file.read()

            st.write("📄 正在解析 PDF...")

            try:
                result = extract_text_from_pdf(pdf_input, uploaded_file.name)
            except Exception as e:
                logging.exception("处理文件失败")
                st.write("处理文件失败")

            st.write("✅完成")
            text=' '
            ls=product_texts(result)
            document = text.join(ls)

            schema = ContractLLMOutput.model_json_schema()
            test_prompt = f"""
    #                 你是一个企业合同信息抽取助手。请根据提供的合同文本提取以下信息:
    #                 {schema}
    #                 只返回结构化结果，不要添加额外解释。            
    #                 合同文本为：
    #                 {document}
    #                 """
            try:
                st.write("🤖正在调用本地 LLM...")
                output = call_llm(test_prompt)
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
            inner_dict = raw_dict.get("properties", raw_dict)
            llm_outputcontract = ContractLLMOutput(**inner_dict)
            # llm_outputcontract = ContractLLMOutput(**raw_dict)
            contractoutput = build_contract(llm_outputcontract)

            print(f"LLM输出结果：{contractoutput.model_dump_json()}")

            print(f"PDF前3000字符原文：{document[:3000]}")

            st.write("🔍 正在建立原文溯源...")
            supply_system(result,contractoutput)
            st.write("✅完成")
            l1 = normalize_amount(contractoutput.amount_value.value)
            l2 = normalize_date(contractoutput.sign_date.value)
            contractoutput.sign_date.value=l2
            contractoutput.amount_value.value=l1

            #计算置信度
            check_output(contractoutput)

            status.update(
                label="处理完成",
                state="complete"
            )
            rows=[]
            for fname in Contract.model_fields.keys():
                fr = getattr(contractoutput, fname)
                val = fr.value if fr.value is not None else "大模型提取失败"
                source_txt = fr.source_text if fr.source_text else ""
                source_page = fr.source_page if fr.source_page else ""
                rows.append({
                    "字段描述": fr.description,
                    "提取值": val,
                    "页码": source_page,
                    "原文片段": source_txt,
                    "溯源状态": fr.trace_status
                })
            st.dataframe(
                rows,
                use_container_width=True,
                column_config={
                    "字段描述": {"width":150},
                    "提取值": {"width":200},
                    "页码":{"width":50},
                    "原文片段": {"width":450},
                    "溯源状态":{"width":220}
                }
            )
            # st.write(contractoutput.contract_number)
            # st.write(contractoutput.party_a)
            # st.write(contractoutput.party_b)
            # st.write(contractoutput.amount_value)
            # st.write(contractoutput.amount_currency)
            # st.write(contractoutput.sign_date)


st.divider()

st.markdown("### How it works")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("**01**")
    st.write("📄 Parse PDF")

with c2:
    st.markdown("**02**")
    st.write("🤖 Extract Fields")

with c3:
    st.markdown("**03**")
    st.write("✓ Validate")

with c4:
    st.markdown("**04**")
    st.write("🔎 Trace Evidence")


st.set_page_config(layout="wide")

# 美化按钮CSS
st.markdown(
    """
<style>
div.stButton > button:first-child {
    background-color: #2b7bba;
    color: white;
    border: none;
    border-radius:10px;
    padding: 0.6rem 2rem;
    font-size:1rem;
}
div.stButton > button:first-child:hover {
    background-color:#1f6296;
}
</style>
""",
    unsafe_allow_html=True
)

