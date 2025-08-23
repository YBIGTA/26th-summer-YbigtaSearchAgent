
import os
import requests
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    GoogleDriveLoader,
    NotionDBLoader,  # NotionDBLoader의 정확한 위치로 수정
    UnstructuredFileIOLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from google.oauth2 import service_account
from googleapiclient.discovery import build

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()
all_docs = []
# --- 1. Notion 데이터 로드 ---
print("="*50)
print("Phase 1: Notion에서 데이터를 불러오는 중입니다...")
try:
    notion_loader = NotionDBLoader(
        integration_token=os.getenv("NOTION_API_KEY"),
        database_id=os.getenv("NOTION_DATABASE_ID"),
        request_timeout_sec=30,
    )
    notion_docs = notion_loader.load()
    
    # --- 👇 [로깅 추가] 불러온 문서 제목 출력 --- 👇
    print(f"✅ Notion에서 {len(notion_docs)}개의 문서를 불러왔습니다. 목록은 다음과 같습니다:")
    for doc in notion_docs:
        # Notion 페이지 제목은 metadata의 'title'에 저장되어 있습니다.
        title = doc.metadata.get('title', '제목 없음') 
        print(f"  - 📄 {title}")
    # --- [로깅 끝] ---

    all_docs.extend(notion_docs)

except Exception as e:
    print(f"❌ Notion 로드 실패: {e}")

# --- 2. Google Drive 데이터 로드 ---
print("\nGoogle Drive에서 데이터를 불러오는 중입니다...")

# --- [진단 코드 시작] ---
try:
    folder_id = os.getenv("GDRIVE_FOLDER_ID")
    print(f"🕵️‍♂️ 서비스 계정 권한으로 '{folder_id}' 폴더의 모든 하위 항목을 확인합니다...")

    creds = service_account.Credentials.from_service_account_file(
        "gdrive-credentials.json", scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=creds)

    def list_files_recursively(folder_id, indent=""):
        try:
            query = f"'{folder_id}' in parents"
            results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
            items = results.get("files", [])
            for item in items:
                print(f"{indent}📄 {item['name']} (ID: {item['id']}, Type: {item['mimeType']})")
                if item["mimeType"] == "application/vnd.google-apps.folder":
                    list_files_recursively(item["id"], indent + "  ")
        except Exception as e:
            print(f"{indent}🚨 오류 발생: 해당 폴더(ID: {folder_id})를 처리하는 중 문제가 생겼습니다. ({e})")

    list_files_recursively(folder_id)
    print("✅ 파일 및 폴더 목록 확인 완료.")

except Exception as e:
    print(f"🚨 [치명적 오류] Google Drive API 연결에 실패했습니다: {e}")
# --- [진단 코드 끝] ---


# --- [LangChain 로더 시작] ---
print("\n📑 LangChain 로더로 문서 로드를 시작합니다...")
gdrive_loader = GoogleDriveLoader(
    folder_id=os.getenv("GDRIVE_FOLDER_ID"),
    service_account_key="gdrive-credentials.json",
    recursive=True,
    file_loader_cls=UnstructuredFileIOLoader,
    file_loader_kwargs={"mode": "elements"},
)

gdrive_docs = gdrive_loader.load()
all_docs.extend(gdrive_docs)
print(f"✅ LangChain이 최종적으로 {len(gdrive_docs)}개의 문서를 로드했습니다.")


# --- 3. GitHub 사용자의 모든 리포지토리 README.md 로드 ---
print("="*50)
print("Phase 3: GitHub 사용자의 모든 리포지토리에서 README.md를 탐색합니다...")

USER_NAME = "YBIGTA"  # 탐색할 GitHub 사용자 계정 이름
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {GITHUB_TOKEN}"
} if GITHUB_TOKEN else {}

def get_all_repos_from_user(user_name):
    """지정된 GitHub 사용자의 모든 공개 리포지토리 이름을 가져옵니다."""
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{user_name}/repos?type=public&page={page}&per_page=100"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if not data:
            break
        repos.extend([repo['full_name'] for repo in data])
        page += 1
    return repos

github_docs = []
try:
    repo_full_names = get_all_repos_from_user(USER_NAME)
    print(f"🔍 총 {len(repo_full_names)}개의 리포지토리를 발견했습니다.")
    
    for repo_name in repo_full_names:
        try:
            loader = GithubFileLoader(
                repo=repo_name,
                access_token=GITHUB_TOKEN,
                file_path="README.md",
                file_filter=lambda file_path: file_path.endswith("README.md")
            )
            docs = loader.load()
            for doc in docs:
                doc.metadata['source'] = f"https://github.com/{repo_name}"
            github_docs.extend(docs)
            print(f"  - ✅ {repo_name}의 README.md 로드 성공")
        except Exception:
            print(f"  - ⚠️ {repo_name}에 README.md가 없거나 로드에 실패했습니다.")
            continue

    all_docs.extend(github_docs)
    print(f"✅ GitHub에서 총 {len(github_docs)}개의 README.md 문서를 불러왔습니다.")

except Exception as e:
    print(f"❌ GitHub 리포지토리 목록을 가져오는 데 실패했습니다: {e}")

# --- 4. 최종 DB 생성 ---
print("="*50)
if all_docs:
    print(f"Phase 4: 총 {len(all_docs)}개의 문서를 기반으로 DB를 생성합니다.")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(all_docs)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(texts, embeddings)
    vectorstore.save_local("faiss_index")
    print("\n🎉 모든 데이터를 기반으로 Vector DB가 성공적으로 저장되었습니다.")
else:
    print("\n⚠️ 로드된 문서가 없어 DB를 생성하지 않았습니다.")