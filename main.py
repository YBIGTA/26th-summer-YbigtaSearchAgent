# main.py

import os # os 라이브러리 import
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Tuple
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
import csv
from datetime import datetime
import os

# --- 설정(Setup) 부분 ---
load_dotenv()

# 임베딩 모델은 기존 OpenAI 모델을 그대로 사용합니다. (참고 사항 확인)
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

# 👇 LLM(언어 모델)을 Upstage Solar로 변경하는 부분
llm = ChatOpenAI(
    model_name="solar-pro2",
    temperature=0,
    api_key=os.getenv("UPSTAGE_API_KEY"),
    base_url="https://api.upstage.ai/v1"
)

# 최종 RAG 체인을 구성합니다.
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever()
)

app = FastAPI()

class ConversationRequest(BaseModel):
    query: str
    chat_history: List[Tuple[str, str]] = []

@app.post("/conversation")
def ask_conversation(request: ConversationRequest):
    result = qa_chain.invoke({
        "question": request.query,
        "chat_history": request.chat_history
    })
    return {"answer": result.get("answer")}

# --- (피드백 API 및 루트 경로는 기존과 동일) ---
class FeedbackRequest(BaseModel):
    query: str
    answer: str
    feedback: str # "good" or "bad"

@app.post("/feedback")
def receive_feedback(request: FeedbackRequest):
    try:
        with open("feedback_log.csv", "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["timestamp", "query", "answer", "feedback"])
            writer.writerow([
                datetime.now().isoformat(),
                request.query,
                request.answer,
                request.feedback
            ])
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/")
def read_root():
    return {"message": "YBIGTA Conversational RAG Agent API is running!"}