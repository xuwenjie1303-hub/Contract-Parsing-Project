import os
import json
from tests.test_LLMwhole import LLM_service

import os

from pathlib import Path

pdf_folder = "./tests/data/mixed"
out_meta_path = "./tests/ground_truth/meta_test.json"
if not os.path.exists(pdf_folder):
    os.makedirs(pdf_folder)
cases = []
for filename in os.listdir(pdf_folder):
    if filename == "13.pdf":
        full_path = os.path.abspath(os.path.join(pdf_folder, filename))
        dict = LLM_service(full_path,1)
        item = dict
        item = item.model_dump(mode="json")
        cases.append(item)

with open(out_meta_path, "w", encoding="utf-8") as f:
    json.dump(cases, f, ensure_ascii=False, indent=2)

print(f"模板已输出到 {out_meta_path}，共{len(cases)}个样本")
