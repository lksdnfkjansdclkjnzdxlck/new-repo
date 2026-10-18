import os
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory, BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import List
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()

parser = StrOutputParser()
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.7
)



# ====================== CUSTOM HISTORY (keeps only last 3 pairs) ======================


class LimitedChatMessageHistory(InMemoryChatMessageHistory):
    max_pairs: int = 3   # declare it as a class field

    def __init__(self, max_pairs: int = 3):
        super().__init__()
        self.max_pairs = max_pairs

    def add_messages(self, messages: List[BaseMessage]) -> None:
        super().add_messages(messages)
        self._trim()

    def add_message(self, message: BaseMessage) -> None:
        super().add_message(message)
        self._trim()

    def _trim(self):
        max_messages = self.max_pairs * 2  # 3 pairs = 6 messages
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]
# ====================== PROMPT ======================
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant specialized in answering questions about a webpage OR a youtube video.
Rules:
1. Do not use outside knowledge to fill gaps in the context.
2. Do not invent facts or unsupported explanations.
3. If the context does not contain enough information,
   clearly state that the answer is not available on the page.
4. Give a concise answer that directly addresses the question.
5. Every factual claim must be supported by the context.
6. If website is not allowing scraping, say that this page do not allow reading webpages instead of saying no reply, say clearly that this page is not allowing to read text from it

Answer the user's question ONLY based on the provided page content or video transcript.
If the content is insufficient, say "I couldn't find that information on the page. or youtube video"
Do not make up answers.
if user says what it is about or summarize it or similar question answerr according to given transcript or page content
Relevant page content or youtube video transcript is given beloe:
{context}"""),
    
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])

chain = prompt | llm | parser

# ====================== SESSION STORE ======================
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = LimitedChatMessageHistory(max_pairs=3)  # ← only last 3 pairs
    return store[session_id]


chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)


# ====================== MAIN FUNCTION ======================
def answer_the_given_question(question: str, context: str, session_id: str = "default") -> str:

    response = chain_with_history.invoke(
        {
            "question": question,
            "context": context
        },
        config={"configurable": {"session_id": session_id}}
    )
    return response


def rewrite_question(question: str) -> str:
    """
    Uses an LLM to rewrite a user question into an optimized search query
    suitable for dense vector retrieval.
    """
    prompt = f"""You are an expert search engine optimizer. 
                Your task is to rewrite the user's question into a concise, direct search query explain the purspose behind question sp that it can be used to find similar informationto answer the question.
                Remove conversational filler (e.g., "please tell me", "can you help me find").
                Focus on core keywords and intent. Return ONLY the rewritten query text.

                User Question: {question}
                Optimized Search Query:"""
    return llm.invoke(prompt).content



def generate_query_variants(question: str, num_variants: int = 5) -> list[str]:
    """Uses an LLM to generate alternative phrasing of the user's question."""
    prompt = f"""You are an AI assistant. Generate {num_variants} different versions of the following 
    user question to help retrieve relevant documents from a vector database. 
    Output ONLY the alternative questions, one per line. Do not include numbering or bullet points.
    
    Original question: {question}"""
    return llm.invoke(prompt).content
