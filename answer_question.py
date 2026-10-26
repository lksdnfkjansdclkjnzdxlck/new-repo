from RewriteQuestion import rewrite_question
from llm import *
from vector_database import  retrieve_chunks
@traceable(name="webby_rag_pipeline",run_type='chain')
async def answer_the_query_stream(
    question: str,
    url: str,
    session_id: str
):
    # 1. Rewrite the question
    rewritten_question = rewrite_question(question)



    # 2. Retrieve relevant chunks
    data = retrieve_chunks(rewritten_question, 10, url)

    # 3. Build context
    context = "\n\n".join(
        f"[Chunk {i + 1}]\n{item['text']}"
        for i, item in enumerate(data)
    )

    # 4. Stream the answer
    async for chunk in answer_the_given_question_stream(
        rewritten_question,
        context,
        session_id
    ):
        yield chunk

'''Added this function js for eveluation coz streaming wasnt working with evaulation script'''
# def answer_my_question(question,url):
#     rewritten_question = rewrite_question(question)



#     # 2. Retrieve relevant chunks
#     data = retrieve_chunks(rewritten_question, 10, url)

#     # 3. Build context
#     context = "\n\n".join(
#         f"[Chunk {i + 1}]\n{item['text']}"
#         for i, item in enumerate(data)
#     )

#     answer = answer_the_given_question(question,context,'default')
#     return answer,context
