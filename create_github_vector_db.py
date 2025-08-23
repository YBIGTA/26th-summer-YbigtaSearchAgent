import os
import requests
import subprocess
import shutil
import json
import sys
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.document_loaders import UnstructuredFileLoader
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
TEMP_REPOS_DIR = "temp_github_repos"
GENERATED_READMES_DIR = "generated_readmes"
FAISS_INDEX_PATH = "github_faiss_index"
PROCESSED_REPOS_CACHE = "processed_repos_cache.json"

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
    print(f"\n💾 {len(documents)}개의 README를 {len(split_docs)}개의 청크로 분할하여 Vector DB에 추가/저장합니다...")
    if vectorstore is None:
        vectorstore = FAISS.from_documents(split_docs, embeddings)
    else:
        vectorstore.add_documents(split_docs)
    vectorstore.save_local(FAISS_INDEX_PATH)
    print("💾 저장 완료.")
    return vectorstore

# --- 메인 로직 ---
print("="*50)
print("GitHub README 생성 및 Vector DB 구축 스크립트를 시작합니다.")

os.makedirs(TEMP_REPOS_DIR, exist_ok=True)
os.makedirs(GENERATED_READMES_DIR, exist_ok=True)

embeddings = CustomUpstageEmbeddings(model="embedding-passage")
vectorstore = None
if os.path.exists(FAISS_INDEX_PATH):
    try:
        vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        print(f"✅ 기존 '{FAISS_INDEX_PATH}' 인덱스를 불러왔습니다.")
    except Exception as e:
        print(f"⚠️ 기존 인덱스 로드 실패 (모델 비호환 가능성): {e}")
        print(f"🔥 기존 '{FAISS_INDEX_PATH}' 인덱스를 삭제하고 새로 생성합니다.")
        shutil.rmtree(FAISS_INDEX_PATH)
        vectorstore = None

if os.path.exists(PROCESSED_REPOS_CACHE):
    with open(PROCESSED_REPOS_CACHE, 'r', encoding='utf-8') as f:
        processed_repos = set(json.load(f))
    print(f"✅ 기존 캐시 파일에서 {len(processed_repos)}개의 처리된 리포지토리 목록을 불러왔습니다.")
else:
    processed_repos = set()

def get_all_repos_from_org(org_name):
    repos = []
    page = 1
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    while True:
        url = f"https://api.github.com/orgs/{org_name}/repos?type=public&page={page}&per_page=100"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if not data:
            break
        repos.extend([(repo['clone_url'], repo['name']) for repo in data])
        page += 1
    return repos

try:
    print("="*50)
    print(f"🏢 {ORG_NAME} 조직의 리포지토리를 가져옵니다...")
    all_repos = get_all_repos_from_org(ORG_NAME)
    print(f"🔍 총 {len(all_repos)}개의 리포지토리를 발견했습니다.")

    for repo_url, repo_name in all_repos:
        print("-" * 50)
        
        if repo_name in processed_repos:
            print(f"⚡️ 캐시 히트! '{repo_name}' 리포지토리는 이미 처리되었습니다. 건너뜁니다.")
            continue

        print(f"🚀 '{repo_name}' 리포지토리 처리 시작...")
        repo_path = os.path.join(TEMP_REPOS_DIR, repo_name)
        output_readme_path = os.path.join(GENERATED_READMES_DIR, f"{repo_name}_README.md")

        try:
            print(f"  - 📂 '{repo_name}'를 복제합니다...")
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
            subprocess.run(["git", "clone", "--depth", "1", repo_url, repo_path], check=True, capture_output=True)

            print(f"  - 🤖 readme-ai(OpenAI)로 README를 생성합니다...")
            
            readme_env = os.environ.copy()
            if not os.getenv("OPENAI_API_KEY"):
                 print("  - 🚨 실패! .env 파일에 OPENAI_API_KEY가 설정되지 않았습니다.")
                 continue
            
            readme_env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

            readme_command = [
                sys.executable, "-m", "readmeai.cli.main",
                "--api", "openai",
                "--model", "gpt-4o-mini",
                "--repository", repo_path,
                "--output", output_readme_path
            ]
            result = subprocess.run(readme_command, capture_output=True, text=True, check=True, env=readme_env)
            print(f"  - ✅ README 생성 성공!")

            loader = UnstructuredFileLoader(output_readme_path)
            doc = loader.load()[0]
            doc.metadata['source'] = f"https://github.com/{ORG_NAME}/{repo_name}"
            
            processed_repos.add(repo_name)
            vectorstore = update_vectorstore(vectorstore, [doc], embeddings)

        except subprocess.CalledProcessError as e:
            print(f"  - 🚨 실패! '{repo_name}' 처리 중 오류가 발생했습니다.")
            print("  - 오류 내용:", e.stderr)
        except Exception as e:
            print(f"  - 🚨 실패! '{repo_name}' 처리 중 예상치 못한 오류 발생: {e}")
        finally:
            if os.path.exists(repo_path):
                print(f"  - 🧹 '{repo_name}' 임시 폴더를 삭제합니다.")
                shutil.rmtree(repo_path)

except Exception as e:
    print(f"\n🚨 스크립트 실행 중 치명적인 오류 발생: {e}")

finally:
    print("="*50)
    print("최종 정리 및 저장을 수행합니다...")
    with open(PROCESSED_REPOS_CACHE, 'w', encoding='utf-8') as f:
        json.dump(list(processed_repos), f, ensure_ascii=False, indent=4)
    print(f"✅ 업데이트된 캐시를 '{PROCESSED_REPOS_CACHE}'에 저장했습니다.")
    print("\n🎉 모든 작업이 완료되었습니다.")
