import hashlib
from pinecone import Pinecone
import os
from langsmith import traceable
from time import perf_counter
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.index("webby-chat")




import hashlib

def store_chunks(url: str, chunks: list[str]):
    records = []

    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.sha256(
            f"{url}::{i}".encode("utf-8")
        ).hexdigest()

        records.append({
            "_id": chunk_id,
            "chunk_text": chunk,
            "url": url,
            "chunk_index": i,
        })

    batch_size = 90

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]

        index.documents.upsert(
            namespace="webby-chat",
            documents=batch,
        )

        print(
            f"Uploaded {min(start + batch_size, len(records))}"
            f"/{len(records)} chunks"
        )

    return len(records)



# @traceable(name="Pinecode_retrieval", run_type="retriever")
def retrieve_chunks(question: str, top_k: int, url: str):
    if not question or not question.strip():
        raise ValueError("The search query cannot be empty.")
    question = str(question)

    results = index.documents.search(
        namespace="webby-chat",
        top_k=top_k,
        score_by=[
            {
                "type": "embed",
                "field": "chunk_text",
                "query": question,
            }
        ],
        filter={
            "url": {"$eq": url}
        },
        include_fields=["chunk_text", "url"],
    )

    data = []

    for doc in results.matches:
        data.append({
            "text": doc.get("chunk_text", ""),
            "score": doc.score,
            "id": doc.id,
        })

    return data
