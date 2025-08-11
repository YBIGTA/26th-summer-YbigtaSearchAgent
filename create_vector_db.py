# create_vector_db.py (최신 로더 적용 버전)

import os
from dotenv import load_dotenv
# langchain_community 대신 langchain_google_community에서 로더를 불러옵니다.
from langchain_google_community import GoogleDriveLoader
from langchain_community.document_loaders import NotionDBLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

# --- 1. Notion 데이터 로드 ---
print("Notion에서 데이터를 불러오는 중입니다...")
notion_loader = NotionDBLoader(
    integration_token=os.getenv("NOTION_API_KEY"),
    database_id=os.getenv("NOTION_DATABASE_ID"),
    request_timeout_sec=30,
)
notion_docs = notion_loader.load()
print(f"Notion에서 {len(notion_docs)}개의 문서를 불러왔습니다.")

# --- 2. Google Drive 데이터 로드 ---
print("Google Drive에서 데이터를 불러오는 중입니다...")
# credentials_path 대신 service_account_key를 사용하여 명확하게 서비스 계정임을 알려줍니다.
gdrive_loader = GoogleDriveLoader(
    folder_id=os.getenv("GDRIVE_FOLDER_ID"),
    service_account_key="gdrive-credentials.json", # 서비스 계정 인증 파일 경로
    recursive=False
)
gdrive_docs = gdrive_loader.load()
print(f"Google Drive에서 {len(gdrive_docs)}개의 문서를 불러왔습니다.")

# --- 3. 두 데이터 소스의 문서를 하나로 합치기 ---
documents = notion_docs + gdrive_docs
print(f"총 {len(documents)}개의 문서를 기반으로 DB를 생성합니다.")

# --- 4. 텍스트 분할 및 임베딩 (기존과 동일) ---
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(texts, embeddings)
vectorstore.save_local("faiss_index")

print("Notion과 Google Drive 데이터를 기반으로 Vector DB가 성공적으로 저장되었습니다.")