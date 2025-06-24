from dotenv import load_dotenv
import os
from typing import TypedDict, List
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableLambda
from langchain.agents import AgentType, initialize_agent
from langchain.tools import StructuredTool

from app.tool import send_sms
from app.model_fields_val_models import SendSMSInput

load_dotenv()

class State(TypedDict, total=False):
    text: str
    answer: str
    next: str

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0
)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
client = QdrantClient(
    url=os.getenv("QDRANT_HOST"),
    api_key=os.getenv("QDRANT_API_KEY")
)

vectorstore = Qdrant(
    client=client,
    collection_name="messages",
    embeddings=embeddings
)

tools = [
    StructuredTool(
        name="send_message",
        func=send_sms,
        description="Отправляет сообщение на номер. Аргументы: employee_username: str - всегда fdax, lead_phone: str - номер фомата +1... без пробелов, message: str - сообщение от отправителя",
        args_schema=SendSMSInput,
    )
]

llm_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

# Агент для RAG режима
rag_chain_with_tools = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

# === 1. ROUTER (Оркестратор) ===
def route(state: dict) -> dict:
    question = state["text"]
    decision = llm.invoke(
        f"Нужно ли использовать базу знаний для вопроса: '{question}'? Ответь 'RAG' или 'LLM'"
    ).content.strip().upper()

    next_step = "rag" if "RAG" in decision else "llm"
    return {"text": question, "answer": "", "next": next_step}

# === 2. Нода: ответ напрямую
def llm_node(state: dict) -> dict:
    result = llm_agent.run(state["text"])
    return {"answer": result}

def rag_node(state: dict) -> dict:
    question = state["text"]
    context_answer = question#rag_chain.run(question)
    final_answer = llm_agent.run(f"На основе этой информации: '{context_answer}' ответь на запрос: '{question}'")
    return {"answer": final_answer}

builder = StateGraph(state_schema=State)

builder.add_node("llm", RunnableLambda(llm_node))
builder.add_node("rag", RunnableLambda(rag_node))
builder.add_node("route", RunnableLambda(route))

builder.set_entry_point("route")
builder.add_conditional_edges("route", lambda state: state["next"], {
    "llm": "llm",
    "rag": "rag"
})
builder.add_edge("llm", END)
builder.add_edge("rag", END)

graph = builder.compile()