from RewriteQuestion import rewrite_question
from llm import *
import re
from vector_database import  retrieve_chunks


@traceable(name="webby_rag_pipeline")
def answer_the_query(question: str, url: str, session_id:str) -> str:
    question = rewrite_question(question)
    data = retrieve_chunks(question,10,url)
    context = "\n\n".join(
        f"[Chunk {i+1}]\n{item['text']}"
        for i, item in enumerate(data)
    )

    answer = answer_the_given_question(question,context,session_id)
    return answer,context




