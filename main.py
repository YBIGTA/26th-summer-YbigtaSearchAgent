# main.py (수정된 버전)

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

# --- 1. 미리 만들어진 Vector DB 로드 ---
def setup_chain():
    load_dotenv()

    # 로컬에 저장된 Vector DB를 불러옵니다.
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

    # RAG 체인 생성
    llm = ChatOpenAI(model_name="gpt-4o-mini-2024-07-18", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever()
    )
    return qa_chain

# (이하 코드는 이전과 동일)
qa_chain = setup_chain()
app = FastAPI()

class QuestionRequest(BaseModel):
    query: str

@app.post("/ask")
def ask_question(request: QuestionRequest):
    answer = qa_chain.invoke(request.query)
    return {"answer": answer['result']}

@app.get("/")
def read_root():
    return {"message": "YBIGTA RAG Agent API is running!"}