import streamlit as st
import sys
from pathlib import Path
import json
proj_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(proj_root))

import streamlit as st
from app.parsers.pdf_parsers import extract_text_from_pdf 
from app.services.llm_service import call_llm
from app.model.contract import ContractLLMOutput,Contract
from app.model.document import product_texts
from app.model.contract import supply_system,build_contract
from app.services.normalizer import normalize_amount,normalize_date
from app.services.validator import check_output
from app.services.json_parser import parse_llm_json

st.set_page_config(
    page_title="PDF Intelligence",
    page_icon="📄",
    layout="wide",
)

# =========================
# Header
# =========================

st.markdown(
    """
    <div style="padding: 2rem 0 1rem 0;">
        <div style="
            font-size: 0.8rem;
            letter-spacing: 0.15rem;
            color: #888;
            font-weight: 600;
        ">
            PDF INTELLIGENCE
        </div>

        <h1 style="
            font-size: 3rem;
            margin: 0.2rem 0;
        ">
            Intelligent Field Extraction
        </h1>

        <p style="
            font-size: 1.1rem;
            color: #777;
            max-width: 700px;
        ">
            Extract structured information from PDF documents
            with local LLM inference and traceable evidence.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"],
    label_visibility="collapsed",
)

if uploaded_file is None:

    st.markdown("### Upload a document")

    st.markdown(
        """
        <div style="
            border: 1px dashed #aaa;
            border-radius: 16px;
            padding: 3rem;
            text-align: center;
            margin: 1rem 0 2rem 0;
        ">
            <div style="font-size: 2.5rem;">📄</div>
            <h3>Drop your PDF here</h3>
            <p style="color:#888;">
                Contracts, invoices, reports and other structured documents
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    st.divider()

    st.markdown("### Example")

    example_col1, example_col2 = st.columns(2)

    with example_col1:
        st.metric("Fields extracted", "6")

    with example_col2:
        st.metric("Evidence verified", "5")

    st.caption(
        "Upload a PDF above to start extracting structured information."
    )
    if uploaded_file is not None:

        st.markdown(f"## 📄 {uploaded_file.name}")

        st.caption("Document ready for extraction")

        if st.button(
            "🚀 Start Extraction",
            type="primary",
            use_container_width=True,
        ):
            # 这里接你原来的逻辑
            ...

st.title("PDF信息提取系统")
uploaded_file=st.file_uploader(
    "upload PDF",
    type=['pdf']
)
if uploaded_file:
    st.write(uploaded_file.name)
    if st.button('读取'):
        with st.status("任务开始", expanded=True) as status:
            pdf_input = uploaded_file.read()

            st.write("📄 正在解析 PDF...")
            result = extract_text_from_pdf(pdf_input, uploaded_file.name)
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

            st.write("🤖正在调用本地 LLM...")
            output = call_llm(test_prompt)
            st.write("✅完成")
            raw_dict = parse_llm_json(output)
            # st.write(raw_dict)
            inner_dict = raw_dict.get("properties", raw_dict)
            llm_outputcontract = ContractLLMOutput(**inner_dict)
            # llm_outputcontract = ContractLLMOutput(**raw_dict)
            contractoutput = build_contract(llm_outputcontract)
            st.divider()

            st.markdown("## Extraction Results")

            left, right = st.columns([1, 2])

            with left:

                st.markdown("### Fields")

                field_names = list(Contract.model_fields.keys())

                selected_field = st.radio(
                    "Select a field",
                    field_names,
                    label_visibility="collapsed",
                )

            with right:

                st.markdown("### 🔎 Evidence")

                fr = getattr(contractoutput, selected_field)

                st.markdown(f"**{selected_field}**")

                st.markdown(
                    f"""
                    <div style="
                        font-size: 1.5rem;
                        font-weight: 600;
                        margin: 0.5rem 0 1rem 0;
                    ">
                        {fr.value}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if fr.trace_status == "FOUND":

                    st.success(
                        f"✓ Verified · Page {fr.source_page}"
                    )

                elif fr.trace_status == "FUZZY_MATCH":

                    st.warning(
                        f"⚠ Fuzzy match · Page {fr.source_page}"
                    )

                else:

                    st.error(
                        "✕ No matching evidence found"
                    )

                if fr.source_text:

                    st.markdown("#### Source text")

                    st.info(fr.source_text)

                if fr.match_score is not None:

                    st.caption(
                        f"Match score: {fr.match_score}"
                    )