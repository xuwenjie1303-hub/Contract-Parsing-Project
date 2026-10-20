import sys
from pathlib import Path
import json
proj_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(proj_root))
import logging
import streamlit as st
from app.services.contract_pipeline import process_contract
from app.model.contract import (
    ContractLLMOutput,
    Contract,
    build_contract,
    supply_system,
)
def single_process(uploaded_file):
    st.write(uploaded_file.name)
    if st.button('读取'):
        with st.status("任务开始", expanded=True) as status:
            pdf_input = uploaded_file.read()

            contractoutput = process_contract(pdf_input,uploaded_file.name)
            st.status("任务完成", expanded=True)
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
            st.session_state["rows"] = rows
            
            if "rows" in st.session_state:
                rows = st.session_state["rows"]
            
            st.subheader("字段提取结果")
            if rows:
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