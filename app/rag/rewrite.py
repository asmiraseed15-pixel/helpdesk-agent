import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

PROMPT = """You rewrite IT helpdesk queries for a search engine.
The user may write in English, Tamil, or Tanglish (Tamil written in English letters).
Rewrite the query as one short, clear English sentence describing the IT problem.
Output only that sentence, nothing else.

Query: {q}"""


def rewrite_query(q: str) -> str:
    return llm.invoke(PROMPT.format(q=q)).content.strip()