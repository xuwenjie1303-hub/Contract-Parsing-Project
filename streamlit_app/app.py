import sys
from pathlib import Path
import json
proj_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(proj_root))
import logging
import streamlit as st
from streamlit_app.single_file_process import single_process
from streamlit_app.multipied_files import multipied_process

logging.basicConfig(
    filename="app.log",
    # filemode="w",   # 每次启动覆盖，清空旧日志
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)



st.title("合同智能信息系统")

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
uploaded_files = st.file_uploader(
    "选择多份合同 PDF",
    type=["pdf"],
    accept_multiple_files=True,
    key="batch_pdf_uploader",
)
st.caption(
    "Upload a PDF above to start extracting structured information."
)


if uploaded_files:
    multipied_process(uploaded_files)

if uploaded_file:
    single_process(uploaded_file)

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

