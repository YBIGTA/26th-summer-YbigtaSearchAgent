import os
import requests
import base64
import shutil
import json
import sys
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List

# --- Python 버전 확인 ---
if sys.version_info < (3, 10):
    print("="*50)
    print("🚨 오류: 이 스크립트는 Python 3.10 이상이 필요합니다.")
    print(f"현재 사용 중인 Python 버전은 {sys.version} 입니다.")
    print("가상환경의 파이썬 버전을 3.10 이상으로 업그레이드해주세요.")
    print("="*50)
    sys.exit(1)

# --- 설정 (Configuration) ---
load_dotenv()
ORG_NAME = "YBIGTA"
FAISS_INDEX_PATH = "github_faiss_index"
PROCESSED_REPOS_CACHE = "processed_repos_cache.json"
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

# --- 맞춤 임베딩 클래스 (올바르게 수정됨) ---
class CustomUpstageEmbeddings(Embeddings):
    def __init__(self, model: str = "embedding-passage", chunk_size: int = 100):  # ✅ 새로운 모델명
        self.model = model
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        self.base_url = "https://api.upstage.ai/v1/embeddings"  # ✅ 직접 API 호출
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


# --- Vector DB 업데이트 및 저장 함수 ---
def update_vectorstore(vectorstore, documents, embeddings):
    if not documents:
        return vectorstore
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = text_splitter.split_documents(documents)
    print(f"  - 💾 README를 {len(split_docs)}개의 청크로 분할하여 Vector DB에 추가합니다...")
    if vectorstore is None:
        vectorstore = FAISS.from_documents(split_docs, embeddings)
    else:
        vectorstore.add_documents(split_docs)
    vectorstore.save_local(FAISS_INDEX_PATH)
    print("  - ✅ 저장 완료.")
    return vectorstore

# --- GitHub API 함수 ---
def get_all_repos_from_org(org_name):
    """조직의 모든 공개 리포지토리 목록을 가져옵니다."""
    repos = []
    page = 1
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    while True:
        url = f"https://api.github.com/orgs/{org_name}/repos?type=public&page={page}&per_page=100"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        except requests.RequestException as e:
            print(f"🚨 GitHub API에서 리포지토리 목록을 가져오는 중 오류 발생: {e}")
            break
    return repos

def get_readme_content(repo_full_name):
    """GitHub API를 통해 리포지토리의 README 파일 내용을 가져옵니다."""
    headers = {"Accept": "application/vnd.github.v3.raw"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    readme_names = ["README.md", "README.rst", "README.txt", "readme.md"]
    for name in readme_names:
        url = f"https://api.github.com/repos/{repo_full_name}/contents/{name}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.text
        except requests.RequestException:
            continue
    return None

# --- 메인 로직 ---
print("="*50)
print("GitHub README 수집 및 Vector DB 구축 스크립트를 시작합니다.")

embeddings = CustomUpstageEmbeddings(model="embedding-passage") # 새로운 모델명 사용
vectorstore = None
if os.path.exists(FAISS_INDEX_PATH):
    try:
        vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        print(f"✅ 기존 '{FAISS_INDEX_PATH}' 인덱스를 불러왔습니다.")
    except Exception as e:
        print(f"⚠️ 기존 인덱스 로드 실패: {e}. 새 인덱스를 생성합니다.")
        shutil.rmtree(FAISS_INDEX_PATH)
        vectorstore = None

if os.path.exists(PROCESSED_REPOS_CACHE):
    with open(PROCESSED_REPOS_CACHE, 'r', encoding='utf-8') as f:
        processed_repos = set(json.load(f))
    print(f"✅ 기존 캐시에서 {len(processed_repos)}개의 처리된 리포지토리 목록을 불러왔습니다.")
else:
    processed_repos = set()

try:
    print("="*50)
    print(f"🏢 {ORG_NAME} 조직의 리포지토리를 가져옵니다...")
    all_repos = get_all_repos_from_org(ORG_NAME)
    print(f"🔍 총 {len(all_repos)}개의 리포지토리를 발견했습니다.")

    for repo in all_repos:
        repo_name = repo['name']
        repo_full_name = repo['full_name']
        print("-" * 50)
        
        if repo_name in processed_repos:
            print(f"⚡️ 캐시 히트! '{repo_name}' 리포지토리는 이미 처리되었습니다. 건너뜁니다.")
            continue

        print(f"🚀 '{repo_name}' 리포지토리 처리 시작...")

        try:
            print(f"  - 📄 README.md 파일 내용을 가져옵니다...")
            readme_content = get_readme_content(repo_full_name)

            if readme_content is None:
                print(f"  - ⚠️ README 파일이 없습니다. 기본 README를 생성합니다.")
                readme_content = f"# {repo_name}\n\n이 리포지토리에 대한 설명이 없습니다."

            doc = Document(
                page_content=readme_content,
                metadata={'source': f"https://github.com/{repo_full_name}"}
            )
            
            vectorstore = update_vectorstore(vectorstore, [doc], embeddings)
            processed_repos.add(repo_name)

        except Exception as e:
            print(f"  - 🚨 실패! '{repo_name}' 처리 중 예상치 못한 오류 발생: {e}")

except Exception as e:
    print(f"\n🚨 스크립트 실행 중 치명적인 오류 발생: {e}")

finally:
    print("="*50)
    print("최종 정리 및 저장을 수행합니다...")
    with open(PROCESSED_REPOS_CACHE, 'w', encoding='utf-8') as f:
        json.dump(list(processed_repos), f, ensure_ascii=False, indent=4)
    print(f"✅ 업데이트된 캐시를 '{PROCESSED_REPOS_CACHE}'에 저장했습니다.")
    print("\n�� 모든 작업이 완료되었습니다.")