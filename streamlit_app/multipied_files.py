import sys
from pathlib import Path
import json
import time
from io import BytesIO
import pandas as pd
proj_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(proj_root))
import logging
import streamlit as st
from app.model.contract import Contract

from app.services.contract_pipeline import process_contract


def contract_to_rows(contract, filename):
    """将一份合同转换为可展示、可导出的字段行。"""
    rows = []

    for field_name in Contract.model_fields:
        field_result = getattr(contract, field_name)
        val = field_result.value if field_result.value is not None else ""
        source_txt = field_result.source_text if field_result.source_text else ""
        source_page = field_result.source_page if field_result.source_page else ""
        rows.append({
            "文件名": filename,
            "字段名": field_name,
            "字段描述": field_result.description,
            "提取值": field_result.value,
            "页码": field_result.source_page,
            "原文片段": field_result.source_text,
            "溯源状态": field_result.trace_status,
        })

    return rows



def multipied_process(uploaded_files):
    st.write(f"已选择 {len(uploaded_files)} 份文件")

    if st.button("开始批量处理", type="primary"):
        all_rows = []
        task_results = []

        progress = st.progress(0)
        status_text = st.empty()

        total = len(uploaded_files)

        for index, uploaded_file in enumerate(uploaded_files):
            filename = uploaded_file.name
            start_time = time.perf_counter()

            status_text.write(
                f"正在处理 {index}/{total}: {filename}"
            )

            try:
                # getvalue() 可以读取完整上传内容，
                # 不依赖当前文件指针的位置。
                pdf_bytes = uploaded_file.getvalue()

                contract = process_contract(
                    pdf_bytes=pdf_bytes,
                    filename=filename,
                )

                all_rows.extend(
                    contract_to_rows(contract, filename)
                )

                task_results.append({
                    "文件名": filename,
                    "状态": "成功",
                    "耗时（秒）": round(
                        time.perf_counter() - start_time, 2
                    ),
                    "错误信息": "",
                })

            except Exception:
                # 记录完整异常到服务端日志，
                # 页面仅展示简洁错误信息。
                import logging
                logging.exception(
                    "合同处理失败: %s", filename
                )

                task_results.append({
                    "文件名": filename,
                    "状态": "失败",
                    "耗时（秒）": round(
                        time.perf_counter() - start_time, 2
                    ),
                    "错误信息": "处理失败，请查看日志",
                })

            finally:
                progress.progress((index + 1) / total)

        status_text.write("批次处理结束")

        st.session_state["batch_task_results"] = task_results
        st.session_state["batch_field_rows"] = all_rows

    if "batch_task_results" in st.session_state:
        task_results = st.session_state["batch_task_results"]
        all_rows = st.session_state["batch_field_rows"]

        success_count = sum(
            item["状态"] == "成功" for item in task_results
        )
        failed_count = len(task_results) - success_count

        col1, col2, col3 = st.columns(3)
        col1.metric("总文件数", len(task_results))
        col2.metric("成功", success_count)
        col3.metric("失败", failed_count)

        st.subheader("文件处理状态")
        st.dataframe(
            pd.DataFrame(task_results),
            use_container_width=True,
        )

        st.subheader("字段提取结果")
        if all_rows:
            st.dataframe(
                pd.DataFrame(all_rows),
                use_container_width=True,
            )

            # 导出 Excel
            excel_buffer = BytesIO()

            with pd.ExcelWriter(
                excel_buffer, engine="openpyxl"
            ) as writer:
                pd.DataFrame(all_rows).to_excel(
                    writer,
                    index=False,
                    sheet_name="合同字段",
                )

                pd.DataFrame(task_results).to_excel(
                    writer,
                    index=False,
                    sheet_name="处理状态",
                )

            st.download_button(
                "下载批处理结果 Excel",
                data=excel_buffer.getvalue(),
                file_name="contract_batch_results.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"
                ),
            )

        # 即使全部文件失败，也能导出任务状态
        st.download_button(
            "下载任务状态 JSON",
            data=json.dumps(
                task_results,
                ensure_ascii=False,
                indent=2,
            ),
            file_name="contract_batch_status.json",
            mime="application/json",
        )
