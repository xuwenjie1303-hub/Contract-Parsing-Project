from pydantic import BaseModel,Field
from app.services.evidence import find_evidence
from operator import attrgetter
import logging
import streamlit as st


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
def supply_system(document, contract: Contract):
    for fname in Contract.model_fields.keys():
        fr:FieldResult = getattr(contract, fname)
        try:
            evidence = find_evidence(document, Contract.model_fields[fname].description, fr.value)
        except Exception as e:
            logging.exception("溯源过程出现失败")
            st.write("溯源过程出现失败")
        if evidence is None:
            continue
        fr: FieldResult = getattr(contract, fname)
        fr.source_page = evidence["page"]
        fr.source_text = evidence["text"]
        fr.trace_status = evidence["status"]
        fr.match_score = evidence["score"]
        setattr(contract,fname,fr)