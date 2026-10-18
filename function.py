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






def preprocess_data(content: str, url: str) -> list:
    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,        # Maximum number of characters per chunk
    chunk_overlap=20,      # Number of characters to overlap between chunks
    length_function=len,   # How to measure chunk size
    is_separator_regex=False,
)
    chunks = text_splitter.split_text(content)
    if not chunks:
        return []
    
    embeddings = np.asarray(model.encode(chunks))



    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"url": url, "chunk_index": i} for i in range(len(chunks))]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,   # important for some chromadb versions
        metadatas=metadatas
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
        ids = preprocess_data(content, url)

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


