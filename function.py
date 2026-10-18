from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
import uuid
from urllib.parse import urlparse
from threading import Lock
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from llm import *
from youtube_transcript import *
import re
import os
import asyncio
import pandas as pd
from get_content import *
from getting_img_des_by_url import get_img_details
from light_embed import TextEmbedding
import numpy as np
import logging
import time

load_dotenv()


# This downloads the model and its required config automatically

model = TextEmbedding(
    model_name_or_path="onnx-models/all-MiniLM-L6-v2-onnx"
)
client = chromadb.PersistentClient(path="./database")
collection = client.get_or_create_collection(
    name="page_data",
    metadata={"hnsw:space": "cosine"}
)

tasks = {}
tasks_lock = Lock()



logger = logging.getLogger("uvicorn.error")



def preprocess_data(content: str, url: str, task_id: str) -> list:
    started = time.perf_counter()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=20,
        length_function=len,
        is_separator_regex=False,
    )

    chunks = text_splitter.split_text(content)

    if not chunks:
        return []

    logger.warning(
        "[%s] Split content into %d chunks",
        task_id, len(chunks)
    )

    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [
        {"url": url, "chunk_index": i}
        for i in range(len(chunks))
    ]

    embedding_batch_size = 16
    db_batch_size = 50

    # Step 1: Generate embeddings in small batches.
    all_embeddings = []

    for start in range(0, len(chunks), embedding_batch_size):
        end = min(start + embedding_batch_size, len(chunks))
        batch = chunks[start:end]

        batch_started = time.perf_counter()

        logger.warning(
            "[%s] Encoding chunks %d-%d of %d",
            task_id, start + 1, end, len(chunks)
        )

        vectors = np.asarray(model.encode(batch))

        logger.warning(
            "[%s] Encoding batch completed in %.2fs; shape=%s",
            task_id,
            time.perf_counter() - batch_started,
            vectors.shape,
        )

        if vectors.ndim != 2 or vectors.shape[0] != len(batch):
            raise ValueError(
                f"Unexpected embedding shape {vectors.shape} "
                f"for {len(batch)} chunks"
            )

        all_embeddings.extend(vectors.tolist())

    logger.warning(
        "[%s] All embeddings generated in %.2fs",
        task_id, time.perf_counter() - started
    )

    # Step 2: Write vectors to ChromaDB in batches.
    for start in range(0, len(chunks), db_batch_size):
        end = min(start + db_batch_size, len(chunks))

        logger.warning(
            "[%s] Writing ChromaDB batch %d-%d",
            task_id, start + 1, end
        )

        collection.add(
            ids=ids[start:end],
            documents=chunks[start:end],
            embeddings=all_embeddings[start:end],
            metadatas=metadatas[start:end],
        )

        logger.warning(
            "[%s] ChromaDB batch %d-%d saved",
            task_id, start + 1, end
        )

    logger.warning(
        "[%s] Preprocessing finished in %.2fs",
        task_id, time.perf_counter() - started
    )

    return ids


def update_progress(task_id, stage, percent, message):
    with tasks_lock:
        if task_id in tasks:
            tasks[task_id].update({
                "stage": stage,
                "progress": percent,
                "message": message,
                "error": False
            })

def process_page(task_id, url):
    try:
        update_progress(task_id, "reading", 10, "Reading webpage...")
        content = (get_content_from_url(url))
        img_data = get_img_details(url)
        content = f'{content} + \n\n\n {img_data}'
     
        
        update_progress(task_id, "extracting", 35, "Extracting readable text...")
        if not content.strip():
            raise ValueError("No readable webpage content found.")

        update_progress(task_id, "embedding", 55, "Generating embeddings and saving...")
        print(content)
        ids = preprocess_data(content, url)
        print(content)
        if not ids:
            raise ValueError("No text chunks were extracted.")

        with tasks_lock:
            tasks[task_id].update({
                "stage": "complete",
                "progress": 100,
                "message": "Analysis complete!",
                "error": False,
                "result": {
                    "url": url,
                    "chunks_stored": len(ids),
                },
            })

    except Exception as error:
        with tasks_lock:
            if task_id in tasks:
                tasks[task_id].update({
                    "stage": "error",
                    "progress": 0,
                    "message": str(error),
                    "error": True,
                })

def answer_the_query(question: str, url: str) -> str:
    question = rewrite_question(question)
    question = generate_query_variants(question)

    embedded_query = np.asarray(model.encode(question))
    
    results = collection.query(
        query_embeddings=[embedded_query],
        n_results=40,
        where={"url": url},
    )
    print(results)
    docs = results["documents"][0] if results["documents"] else []
  
   
    if not docs:
        answer = "I couldn't find any relevant information on this page for that question."
        context = ['not found']
        return answer,context
    
    
    
    context = "\n\n---\n\n".join(docs)


    answer = answer_the_given_question(question,context)
    return answer,context


