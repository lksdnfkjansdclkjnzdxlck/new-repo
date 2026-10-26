from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid
from threading import Lock
from llm import *
from youtube_transcript import *
import os
import asyncio
import pandas as pds
import numpy as np
from vector_database import store_chunks,video_chunks_exist
load_dotenv()




tasks = {}
tasks_lock = Lock()






def preprocess_data(content: str, url: str) -> list:
    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,        # Maximum number of characters per chunk
    length_function=len,   # How to measure chunk size
    is_separator_regex=False,
)
    chunks = text_splitter.split_text(content)
    records_length = store_chunks(url,chunks)
    return records_length

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
        if video_chunks_exist(url):
            with tasks_lock:
                tasks[task_id].update({
                    "stage": "complete",
                    "progress": 100,
                    "message": "Existing chunks found. Ready to chat!",
                    "error": False,
                    "result": {
                        "url": url,
                        "chunks_stored": 0,
                        "cached": True,
                    },
                })
        else:        
            update_progress(task_id, "reading", 10, "Reading webpage...")
            content = (get_content_from_url(url))
    
        
            
            update_progress(task_id, "extracting", 35, "Extracting readable text...")
            if not content.strip():
                raise ValueError("No readable webpage content found.")

            update_progress(task_id, "embedding", 55, "Generating embeddings and saving...")
            records_length = preprocess_data(content, url)

            if not records_length:
                raise ValueError("No text chunks were extracted.")

            with tasks_lock:
                tasks[task_id].update({
                    "stage": "complete",
                    "progress": 100,
                    "message": "Analysis complete!",
                    "error": False,
                    "result": {
                        "url": url,
                        "chunks_stored": records_length,
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



