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
import logging
from logging.handlers import RotatingFileHandler
from langchain_upstage import UpstageEmbeddings
from langchain.retrievers import EnsembleRetriever 

# --- 설정(Setup) 부분 ---
load_dotenv()

# 임베딩 모델은 기존 OpenAI 모델을 그대로 사용합니다. (참고 사항 확인)
embeddings = UpstageEmbeddings(    
    api_key=os.getenv("UPSTAGE_API_KEY"),
    model="embedding-query"
)

# 👇 LLM(언어 모델)을 Upstage Solar로 변경하는 부분
llm = ChatOpenAI(
    model_name="solar-pro2",
    temperature=0,
    api_key=os.getenv("UPSTAGE_API_KEY"),
    base_url="https://api.upstage.ai/v1"
)

# 두 개의 Vectorstore 불러오기
notion_vs = FAISS.load_local("notion_faiss_index", embeddings, allow_dangerous_deserialization=True)
gdrive_vs = FAISS.load_local("gdrive_faiss_index", embeddings, allow_dangerous_deserialization=True)

# retriever를 Ensemble로 묶기
retriever = EnsembleRetriever(
    retrievers=[
        notion_vs.as_retriever(search_kwargs={"k": 3}),
        gdrive_vs.as_retriever(search_kwargs={"k": 3})
    ],
    weights=[0.5, 0.5]   # 👈 필요하면 가중치 조정 (예: [0.7, 0.3])
)

# Conversational Retrieval Chain 구성
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever
)


# --- 로깅 설정 ---
logger = logging.getLogger("rag-logger")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("rag_usage.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8")
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

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
    answer = result.get("answer")

    # --- 토큰 사용량 로깅 ---
    metadata = result.get("source_documents", None)  # 보통 여기에 문서 출처
    response_metadata = result.get("response_metadata", {})  # 여기에 usage 정보가 들어올 수 있음
    usage = response_metadata.get("token_usage") or response_metadata.get("usage")

    logger.info(
        f"query='{request.query}' | answer_len={len(answer)} "
        f"| usage={usage}"
    )
    return {"answer": answer}

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