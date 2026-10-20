from pydantic import BaseModel,Field
from app.services.evidence import find_evidence
from operator import attrgetter
import logging
import streamlit as st
from app.services.llm_service import call_llm
from app.services.json_parser import parse_llm_json


class FieldResult(BaseModel):
    value: str | float | None=None
    source_page: int | None=None
    source_text: str | None=None
    confidence: float| None=None
    description: str| None=None
    error: str|None=None
    trace_status: str = "NOT_FOUND"
    match_score: float | None = None


class Contract(BaseModel):
    contract_number: FieldResult = Field(description="合同编号")
    party_a: FieldResult = Field(description="主体A")
    party_b: FieldResult = Field(description="主体B")
    amount_value: FieldResult = Field(description="交易金额")
    amount_currency: FieldResult = Field(description="货币单位")
    sign_date: FieldResult = Field(description="签署日期")


class ContractLLMOutput(BaseModel):
    contract_number: str | None = Field(..., description="合同编号")
    party_a: str | None = Field(..., description="主体A")
    party_b: str | None = Field(..., description="主体B")
    amount_value: str | None = Field(..., description="交易金额")
    amount_currency: str | None = Field(..., description="货币单位")
    sign_date: str | None = Field(..., description="合同签署落款日期，排除工期、交付、验收、付款等其他日期")


class ExtractionResponse(BaseModel):
    success: bool
    fields: dict[str, FieldResult]
    error: str | None = None


#将LLM输出数据结构转换为正常contract数据结构
def build_contract(llm_out: ContractLLMOutput) -> Contract:
    field_data = {}
    for fname in Contract.model_fields.keys():
        val = getattr(llm_out, fname)
        field_data[fname] = FieldResult(
            value=val,
            source_page=None,
            source_text=None,
            confidence=None,
            description=Contract.model_fields[fname].description,
            error=None,
            trace_status = "NOT_FOUND",
            match_score = None
        )
        
    return Contract(**field_data)



#完善空值
def supply_system(evidence, contract: Contract):
    for fname in Contract.model_fields.keys():
        if evidence[fname] is None:
            continue
        fr: FieldResult = getattr(contract, fname)
        prompt = build_evidence_prompt(fname, fr.value, evidence[fname])
        # 4. 调用 LLM
        raw_output = call_llm(prompt)
        # 5. 解析 JSON
        raw_data = parse_llm_json (raw_output)
    
        inner_dict = raw_data.get ("properties", raw_data)
        if inner_dict is not None:
            for id in inner_dict["evidence_ids"]:
                num = extract_number(id)
                if num is None:
                    continue
                idx = num - 1
                print(idx)
                fr.trace_status = "FOUND"
                fr.source_page = evidence[fname][idx]["page"]
                fr.source_text = evidence[fname][idx]["text"]
            setattr(contract,fname,fr)

import re

def extract_number(raw_id: str):
    # 正则提取字符串里面所有数字，拿到末尾序号
    nums = re.findall(r"\d+", raw_id)
    if nums:
        return int(nums[-1])
    return None


def build_evidence_prompt(
    field: str,
    value: str,
    matches: list[dict],
) -> str:
    
    sections=['----------------------------',f'{field}']
    for i, item in enumerate(matches, start=1):
        block = f"ID: '{i}' | 页码: {item.get('page')}\n{item['text']}"
        sections.append(block)
    excerpts = "\n\n".join(sections)
    
    print(excerpts)
    return f"""
你是合同证据核验助手。
待核验字段: {field}
已提取的值: {value}
任务：只从原文片段里，找到**直接支持该字段业务含义**的原文，
⚠️禁止仅仅因为文本里面出现数字、日期字符串就选中该片段！
⚠️排除规则：
- 如果是质保期限、验收时限、工期天数、付款截止时间，**不要选**，这些不是本字段的证据。
请从以下原文中判断，哪些片段能够直接支持该字段的值，而不只是碰巧出现相同的字符串。
{excerpts}

【强制要求】
1. evidence_ids 只能填写【证据列表前面的数字序号】，只能是纯数字字符串！
2. ❌禁止填写文档id、pdf名字、文本内容，禁止返回类似 "caigouhetong.pdf_55" 的内容
✅正确示例：["1","2"]
❌错误示例：["ID: caigouhetong.pdf_55"]

只返回JSON：
例如：
{{
  "supported": true,
  "evidence_ids": ["2"]
}}
如果没有足够证据，请返回 supported=false, evidence_ids=[]。
只能引用提供的序号，不得编造。

"""