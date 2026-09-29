import os
import json
from tests.test_LLMwhole import LLM_service

import os

from pathlib import Path

pdf_folder = "./tests/data/scanned"
out_meta_path = "./tests/ground_truth/meta_scanned.json"
if not os.path.exists(pdf_folder):
    os.makedirs(pdf_folder)
cases = []
for filename in os.listdir(pdf_folder):
    full_path = os.path.abspath(os.path.join(pdf_folder, filename))
    dict = LLM_service(full_path,0)
    item = dict
    
    # item = {
    #     "document_id": doc_id,
    #     "pdf_path": full_path,
    #     "ground_truth": {
    #         "contract_no": {"value": "", "expect_trace_status": "FOUND"},
    #         "party_a": {"value": "", "expect_trace_status": "FOUND"},
    #         "party_b": {"value": "", "expect_trace_status": "FOUND"},
    #         "amount_value": {"value": "", "expect_trace_status": "FOUND"},
    #         "amount_currency":{"value": "", "expect_trace_status": "FOUND"},
    #         "sign_date": {"value": "", "expect_trace_status": "FOUND"}
    #     }
    # }
    cases.append(item)

with open(out_meta_path, "w", encoding="utf-8") as f:
    json.dump(cases, f, ensure_ascii=False, indent=2)

print(f"模板已输出到 {out_meta_path}，共{len(cases)}个样本")
