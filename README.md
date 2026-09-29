# Contract-Parsing-Project
Local LLM‑powered contract parsing tool. Extract structured fields from native PDF contracts with evidence traceability, built with Streamlit &amp; Pydantic.

# PDF合同信息抽取工具
> 本地离线PDF合同结构化抽取，基于PyMuPDF + Pydantic，支持普通PDF、扫描OCR文本。
实现关键词溯源、模糊溯源、LLM兜底三级抽取策略，输出带溯源证据的结构化结果。

## ✨功能特性
- 读取PDF（原生文本PDF / OCR扫描PDF）
- 字段别名匹配：合同编号、甲乙双方、交易金额、货币单位、签署日期
- 三级抽取策略：精确关键词溯源 → 模糊匹配溯源 → LLM兜底抽取
- 完整溯源信息输出：来源页码、原文片段、匹配分数、状态标记 `FOUND / fuzz found / NOT_FOUND`
- 日期归一化：多种中文/外文日期格式统一输出`YYYY‑MM‑DD`，自动处理各类破折号兼容脏OCR文本
- 金额解析：阿拉伯数字 + 中文大写金额识别
- 强类型Pydantic输出结构，支持保存完整结果JSON，也输出极简真值用于准确率评测
- 测试集评估脚本，批量跑测试PDF，统计抽取准确率

## 📦环境安装
```bash
# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
