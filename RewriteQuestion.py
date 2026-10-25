from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langsmith import traceable
load_dotenv()

parser = StrOutputParser()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.7,
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert search query optimizer for RAG systems.

Given the user's question, perform BOTH tasks:

1. Rewrite the question into one concise, direct search query.
2. Generate 6 alternative search queries that preserve the user's
   original intent while exploring different relevant phrasings.

Instructions:
- Remove conversational filler.
- Preserve the original meaning and technical terminology.
- Include relevant entities and context.
- Make alternatives meaningfully different, not simple repetitions.
- Do not answer the question.
- Do not include explanations, numbering, or bullet points.

Return EXACTLY this format:

<alternative query 1>
<alternative query 2>
<alternative query 3>
<alternative query 4>
<alternative query 5>
<alternative query 6>"""
    ),
    ("human", "{question}")
])

chain = prompt | llm | parser

@traceable(name="rewrite_question", run_type="chain")
def rewrite_question(question:str)->str:
    new_question = chain.invoke(question)
    return new_question
