import os
from dotenv import load_dotenv
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import trim_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_groq import ChatGroq
from langsmith import traceable
from fastapi.responses import StreamingResponse

# 1. Load environment variables (API keys)
load_dotenv()

# 2. Initialize the LLM
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.7)

# 3. Create a template for the prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant specialized in answering questions about a webpage OR a youtube video.
Rules:
1. Do not use outside knowledge to fill gaps in the context.
2. Do not invent facts or unsupported explanations.
3. If the context does not contain enough information, state that the answer is not available on the page.
4. Give a concise answer that directly addresses the question.
5. Every factual claim must be supported by the context.
6. Dont answer like 'this script says', instead answer like 'in the given video'
Answer the user's question ONLY based on the provided video transcript:
{context}"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])

# 4. Define the message trimmer to keep only the last 3 pairs (6 messages)
trimmer = trim_messages(
    max_tokens=6,
    token_counter=len,  # Counts by number of messages instead of actual text tokens
    strategy="last",
    allow_partial=False,
    start_on="human"
)

# 5. Build the core processing chain
chain = (
    RunnablePassthrough.assign(history=lambda x: trimmer.invoke(x["history"]))
    | prompt 
    | llm 
    | StrOutputParser()
)

# 6. Set up the session memory store
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 7. Wrap the chain to manage session history automatically
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)

# 8. Main execution function
@traceable(name="generate_answer")
async def answer_the_given_question_stream(
    question: str,
    context: str,
    session_id: str = "default"
):
    async for chunk in chain_with_history.astream(
        {
            "question": question,
            "context": context,
        },
        config={
            "configurable": {
                "session_id": session_id
            }
        }
    ):
        if chunk:
            yield chunk


'''Added this function js for eveluation coz streaming wasnt working with evaulation script'''
# def answer_the_given_question(
#     question: str,
#     context: str,
#     session_id: str = "default"
# ) -> str:
#     response = chain_with_history.invoke(
#         {
#             "question": question,
#             "context": context,
#         },
#         config={
#             "configurable": {
#                 "session_id": session_id
#             }
#         }
#     )

#     return response
