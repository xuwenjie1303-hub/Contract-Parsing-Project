import re
import chromadb
import ollama
from app.model.document import Document,PageText
from app.model.contract import ContractLLMOutput
from typing import Union
from app.services.data import FIELD_QUERIES
from app.services.evidence import find_evidence
from app.model.contract import (
    ContractLLMOutput,
    Contract,
    build_contract,
    supply_system,
)
def chunk_contract_pages(
    pages: list[PageText],
    max_chars: int = 100,
    overlap: int = 10,
) -> list[dict]:
    chunks = []

    for page_data in pages:
        page_num = page_data.page_number
        text = page_data.text.strip()

        if not text:
            continue

        # 优先按段落切分，避免完全切断条款
        paragraphs = re.split(r"\n\s*\n", text)
        current = ""
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            if len(current) + len(paragraph) + 1 <= max_chars:
                current = f"{current}\n{paragraph}".strip()
                continue

            if current:
                chunks.append({
                    "page": page_num,
                    "text": current,
                })

            # 对超长段落进行二次切分
            if len(paragraph) > max_chars:
                start = 0

                while start < len(paragraph):
                    piece = paragraph[start:start + max_chars]

                    chunks.append({
                        "page": page_num,
                        "text": piece,
                    })

                    start += max_chars - overlap

                current = ""
            else:
                current = paragraph

        if current:
            chunks.append({
                "page": page_num,
                "text": current,
            })

    return chunks


class ContractRetriever:
    def __init__(
        self,
        persist_dir: str = "./data/chroma",
    ):
        self.client = chromadb.PersistentClient(
            path=persist_dir
        )

    @staticmethod
    def embed(texts: list[str]) -> list[list[float]]:
        response = ollama.embed(
            model="nomic-embed-text",
            input=texts,
        )
        return response["embeddings"]

    def index_contract(
        self,
        chunks,
        document_id,
    ):
        collection_name = f"contract_{document_id}"

        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        if not chunks:
            raise ValueError("合同没有可建立索引的文本")

        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embed(texts)

        collection.upsert(
            ids=[
                f"{document_id}_{i}"
                for i in range(len(chunks))
            ],
            documents=texts,
            metadatas=[
                {
                    "document_id": document_id,
                    "page": chunk["page"],
                }
                for chunk in chunks
            ],
            embeddings=embeddings,
        )

        return collection_name



    def retrieve(
        self,
        collection_name: str,
        query: Union[str, list[str]],
        top_k: int = 1,
    ) -> list[dict]:
        collection = self.client.get_collection(
            name=collection_name
        )

        # 统一成 list
        queries = [query] if isinstance(query, str) else query

        if not queries:
            return []

        # 避免空 collection 导致 n_results = 0
        collection_count = collection.count()
        if collection_count == 0:
            return []

        # 一次性计算所有 query 的 embedding
        query_embeddings = self.embed(queries)

        all_evidence = []
        seen_ids = set()

        # 每个 query 分别检索
        for q, embedding in zip(queries, query_embeddings):
            result = collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k, collection_count),
                include=[
                    "documents",
                    "metadatas",
                    "distances",
                ],
            )

            ids = result["ids"][0]
            documents = result["documents"][0]
            metadatas = result["metadatas"][0]
            distances = result["distances"][0]

            for doc_id, text, metadata, distance in zip(
                ids, documents, metadatas, distances
            ):
                # 按文档 ID 去重
                if doc_id in seen_ids:
                    continue

                seen_ids.add(doc_id)
       
                all_evidence.append({
                    "id": doc_id,
                    "text": text,
                    "page": metadata.get("page"),
                    "distance": distance,
                    "query": q,
                })

        return all_evidence


def retrieve_field_evidence(document,
    retriever: ContractRetriever,
    collection_name: str,
) -> dict:
    evidence_by_field = {}
  

    for field, query in FIELD_QUERIES.items():
        evidence_by_field[field] = retriever.retrieve(
            collection_name=collection_name,
            query=query,
            top_k=1,
        )
    for fname in Contract.model_fields.keys():
        evidence = []
        evidence = find_evidence(document, Contract.model_fields[fname].description)
        modified = []
        for i,item in enumerate(evidence):
            modified.append({"id": document.filename,
                            "text": item["text"],
                            "page": item["page"],
                            "distance": None,
                            "query": None,})
                
        evidence_by_field[fname].extend(modified)

    
    return evidence_by_field


def format_evidence(evidence_by_field: dict) -> str:
    sections = []

    for field, evidence_list in evidence_by_field.items():
        sections.append(f"字段：{field}")

        if not evidence_list:
            sections.append("未检索到相关证据")
            continue
        for i, item in enumerate(evidence_list, start=1):
            # sub是子列表
            doc_id = item["id"]
            page = item["page"]
            distance = item["distance"]
            text = item["text"]

            sections.append(
                f"证据ID {i} | 第 {page} 页\n"
                f"{text}"
            )
    return "\n\n".join(sections)


def build_rag_prompt(document_result:Document, retriever: ContractRetriever,) -> str:
    chunks = chunk_contract_pages(document_result.pages)

    for chunk in chunks:
        chunk["text"] = " ".join(chunk["text"].split())

    name = document_result.filename
    collection_name = retriever.index_contract(chunks, name)
    evidence_by_field = retrieve_field_evidence(document_result, retriever, collection_name)

    evidence_text = format_evidence(evidence_by_field)
    # 3. 构造 Prompt
    schema = ContractLLMOutput.model_json_schema()
    return (f"""
你是一个严谨的合同信息抽取助手，根据{evidence_text}必须返回以下全部 6 个字段：
{schema}
给你形容一下：
    contract_number: "合同编号"
    party_a: "主体A"，采购方、甲方名称，
    party_b: "主体B"，供货方、乙方名称
    amount_value: "交易金额",合同总价、总金额等
    amount_currency: "货币单位"
    sign_date: "签署日期"
规则：
1. 必须输出全部 6 个字段，禁止省略，直接给值，不要type,description等信息
2. 只有证据明确支持时才填写具体值。
3. 证据不足时填写 null，不得猜测。
4. 字段名称必须与上述名称完全一致。
5. sign_date 是合同签署落款日期，不是履行日期或生效日期。
7. 只输出 JSON，不要输出 Markdown 或额外解释。

只能引用提供的证据，不得编造原文。

""",evidence_by_field)


# f"""
# 你是一个严谨的合同信息抽取系统。

# 请根据提供的合同原文证据抽取合同字段。

# 要求：
# 1. 只能根据提供的证据作答，不得猜测。
# 2. 证据不足时，按照 JSON Schema 要求返回 null。
# 3. 不要混淆合同总金额、分期付款金额和违约金。
# 4. 不要混淆签署日期、生效日期和服务开始日期。
# 5. 如果证据之间存在冲突，不要擅自选择。
# 6. source_text 必须来自提供的原文证据。
# 7. source_page 必须使用证据中的页码。
# 8. 只输出 JSON，不要输出 Markdown 或额外解释。

# 合同证据：

# {evidence_text}
# """