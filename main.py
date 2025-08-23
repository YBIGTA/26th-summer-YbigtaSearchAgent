# main.py (피드백 기능 추가 버전)

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Tuple
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from openai import OpenAI
import csv
from datetime import datetime
import os

# --- (기존 setup 및 app 초기화 코드는 동일) ---
load_dotenv()

# Upstage API 클라이언트 설정
upstage_client = OpenAI(
    api_key=os.getenv("UPSTAGE_API_KEY"),
    base_url="https://api.upstage.ai/v1"
)

# 커스텀 Upstage 임베딩 클래스
class UpstageEmbeddings:
    def __init__(self, client, model="embedding-query"):
        self.client = client
        self.model = model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서들을 임베딩합니다."""
        embeddings = []
        for text in texts:
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            embeddings.append(response.data[0].embedding)
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """쿼리를 임베딩합니다."""
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding

# Upstage 임베딩 인스턴스 생성
embeddings = UpstageEmbeddings(upstage_client)
vectorstore = FAISS.load_local("notion_faiss_index", embeddings, allow_dangerous_deserialization=True)
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever()
)
app = FastAPI()

class ConversationRequest(BaseModel):
    query: str
    chat_history: List[Tuple[str, str]] = []

# --- (기존 /conversation 경로는 동일) ---
@app.post("/conversation")
def ask_conversation(request: ConversationRequest):
    result = qa_chain.invoke({
        "question": request.query,
        "chat_history": request.chat_history
    })
    return {"answer": result.get("answer")}

# --- 👇 새로운 피드백 API 엔드포인트 추가 👇 ---
class FeedbackRequest(BaseModel):
    query: str
    answer: str
    feedback: str # "good" or "bad"

@app.post("/feedback")
def receive_feedback(request: FeedbackRequest):
    """
    사용자 피드백을 받아 'feedback_log.csv' 파일에 저장합니다.
    """
    # 파일이 없으면 헤더와 함께 새로 생성합니다.
    try:
        with open("feedback_log.csv", "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            # 파일이 비어있으면 헤더를 작성합니다.
            if f.tell() == 0:
                writer.writerow(["timestamp", "query", "answer", "feedback"])

            # 데이터 행을 작성합니다.
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