import os
import requests
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.document_loaders import UnstructuredFileLoader
from typing import List
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import tempfile

# --- 설정(Configuration) ---
load_dotenv()
FAISS_INDEX_PATH = "gdrive_faiss_index"
BATCH_SIZE = 5
# 파싱된 결과를 저장할 캐시 파일 경로
PARSED_CACHE_FILE = "parsed_cache.json"

# --- 맞춤 임베딩 클래스 ---
class CustomUpstageEmbeddings(Embeddings):
    def __init__(self, model: str = "embedding-passage", chunk_size: int = 100):
        self.model = model
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        self.base_url = "https://api.upstage.ai/v1/embeddings"
        self.chunk_size = chunk_size

    def _embed(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            raise ValueError(".env 파일에 UPSTAGE_API_KEY가 설정되지 않았습니다.")
        
        all_embeddings = []
        # API의 토큰 제한을 초과하지 않도록 텍스트를 작은 배치로 나누어 처리
        for i in range(0, len(texts), self.chunk_size):
            batch = texts[i:i + self.chunk_size]
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            data = {"input": batch, "model": self.model}
            
            response = requests.post(self.base_url, headers=headers, json=data)
            
            if response.status_code == 200:
                response_data = response.json().get("data", [])
                batch_embeddings = [None] * len(batch)
                for item in response_data:
                    batch_embeddings[item['index']] = item['embedding']
                all_embeddings.extend(batch_embeddings)
            else:
                raise Exception(f"Upstage Embeddings API 오류: {response.status_code} - {response.text}")
        
        return all_embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        query_model = self.model.replace("passage", "query")
        temp_model = self.model
        self.model = query_model
        embedding = self._embed([text])[0]
        self.model = temp_model
        return embedding

# --- Upstage Document Parser 호출 함수 ---
def parse_with_upstage(file_path, original_file_name):
    print(f"  - 🤖 Upstage Parser로 '{original_file_name}' 파일 처리 중...")
    url = "https://api.upstage.ai/v1/document-digitization"
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        print("  - 🚨 오류: .env 파일에 UPSTAGE_API_KEY가 설정되지 않았습니다.")
        return None
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {"model": "document-parse"}
            response = requests.post(url, headers=headers, files=files, data=data)
        if response.status_code == 200:
            content = response.json().get("content", {})
            full_text = content.get("markdown") or content.get("html") or ""
            if not full_text:
                elements = response.json().get("elements", [])
                full_text = "\n".join([el.get("content", {}).get("text", "") for el in elements])
            print(f"  - ✅ '{original_file_name}' 처리 완료.")
            return full_text
        else:
            print(f"  - 🚨 Upstage Parser 오류: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"  - 🚨 Upstage API 호출 중 예외 발생: {e}")
        return None

# --- Vector DB 업데이트 및 저장 함수 ---
def update_vectorstore(vectorstore, documents, embeddings):
    if not documents:
        return vectorstore

    # 👇 [수정] DB에 추가하기 전에 텍스트를 작은 조각(chunk)으로 분할합니다.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = text_splitter.split_documents(documents)
    
    print(f"\n💾 {len(documents)}개의 문서를 {len(split_docs)}개의 청크로 분할하여 Vector DB에 추가/저장합니다...")
    
    if vectorstore is None:
        # DB가 없으면 새로 생성
        vectorstore = FAISS.from_documents(split_docs, embeddings)
    else:
        # 기존 DB에 문서 추가
        vectorstore.add_documents(split_docs)
    
    vectorstore.save_local(FAISS_INDEX_PATH)
    print("💾 저장 완료.")
    return vectorstore

# --- 메인 로직 ---
print("="*50)
print("Vector DB 생성/업데이트 스크립트를 시작합니다.")

# 1. 임베딩 모델 및 기존 DB 로드
print("🛰️ Upstage Solar 임베딩 모델을 설정합니다...")
embeddings = CustomUpstageEmbeddings(model="embedding-passage")
vectorstore = None
if os.path.exists(FAISS_INDEX_PATH):
    try:
        vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        print(f"✅ 기존 '{FAISS_INDEX_PATH}' 인덱스를 성공적으로 불러왔습니다.")
    except Exception as e:
        print(f"⚠️ 기존 인덱스 로드 실패: {e}. 새 인덱스를 생성합니다.")
else:
    print(f"ℹ️ 기존 인덱스가 없습니다. 새 인덱스를 생성합니다.")

# 캐시 파일 로드
if os.path.exists(PARSED_CACHE_FILE):
    with open(PARSED_CACHE_FILE, 'r', encoding='utf-8') as f:
        parsed_cache = json.load(f)
    print(f"✅ 기존 캐시 파일 '{PARSED_CACHE_FILE}'에서 {len(parsed_cache)}개의 항목을 불러왔습니다.")
else:
    parsed_cache = {}

# 2. Google Drive 데이터 처리
print("="*50)
print("Google Drive에서 데이터를 불러오는 중입니다...")
batch_docs = []

try:
    folder_id = os.getenv("GDRIVE_FOLDER_ID")
    creds = service_account.Credentials.from_service_account_file(
        "gdrive-credentials.json", scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=creds)

    with tempfile.TemporaryDirectory() as temp_dir:
        def process_folder(folder_id):
            global vectorstore, batch_docs, parsed_cache
            query = f"'{folder_id}' in parents"
            results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
            items = results.get("files", [])

            for item in items:
                original_file_name = item['name']
                file_id = item['id']
                mime_type = item['mimeType']
                
                if mime_type == "application/vnd.google-apps.folder":
                    print(f"📂 하위 폴더 '{original_file_name}' 탐색 시작...")
                    process_folder(file_id)
                    continue

                print(f"  - 📄 파일 '{original_file_name}' 발견.")
                
                if file_id in parsed_cache:
                    print(f"  - ⚡️ 캐시 히트! '{original_file_name}'는 이미 처리된 문서입니다.")
                    page_content = parsed_cache[file_id]
                    doc = Document(page_content=page_content, metadata={"source": original_file_name})
                    batch_docs.append(doc)
                else:
                    sanitized_file_name = original_file_name.replace("/", "_")
                    _, file_ext = os.path.splitext(sanitized_file_name)
                    ext = file_ext.lower()
                    
                    doc_content = None
                    if ext in ['.pdf', '.docx', '.pptx', '.xlsx', '.py', '.txt']:
                        request = service.files().get_media(fileId=file_id)
                        fh = io.BytesIO()
                        downloader = MediaIoBaseDownload(fh, request)
                        done = False
                        while not done:
                            status, done = downloader.next_chunk()
                        temp_file_path = os.path.join(temp_dir, sanitized_file_name)
                        with open(temp_file_path, "wb") as f:
                            f.write(fh.getvalue())
                        
                        if ext in ['.pdf', '.docx', '.pptx', '.xlsx']:
                            doc_content = parse_with_upstage(temp_file_path, original_file_name)
                        elif ext in ['.py', '.txt']:
                            print(f"  - 📝 일반 텍스트 로더로 '{original_file_name}' 파일 처리 중...")
                            loader = UnstructuredFileLoader(temp_file_path)
                            loaded_docs = loader.load()
                            if loaded_docs:
                                doc_content = loaded_docs[0].page_content
                            print(f"  - ✅ '{original_file_name}' 처리 완료.")
                    else:
                        print(f"  - ⏭️ 지원하지 않는 파일 형식({ext})이므로 건너뜁니다.")

                    if doc_content is not None:
                        print(f"  - 💾 캐시에 '{original_file_name}'의 파싱 결과를 저장합니다.")
                        parsed_cache[file_id] = doc_content
                        doc = Document(page_content=doc_content, metadata={"source": original_file_name})
                        batch_docs.append(doc)

                if len(batch_docs) >= BATCH_SIZE:
                    vectorstore = update_vectorstore(vectorstore, batch_docs, embeddings)
                    batch_docs = []
        
        process_folder(folder_id)

finally:
    print("="*50)
    print("최종 정리 및 저장을 수행합니다...")
    vectorstore = update_vectorstore(vectorstore, batch_docs, embeddings)
    
    with open(PARSED_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(parsed_cache, f, ensure_ascii=False, indent=4)
    print(f"✅ 업데이트된 캐시를 '{PARSED_CACHE_FILE}'에 저장했습니다.")
    
    print("\n🎉 스크립트 실행이 완료되었습니다.")
