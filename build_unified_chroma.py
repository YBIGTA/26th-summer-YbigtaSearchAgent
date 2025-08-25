import os
import io
import json
import time
import uuid
import argparse
import tempfile
import asyncio
import itertools
from typing import List, Dict, Any, Optional, Tuple

import requests
import aiohttp
from dotenv import load_dotenv

# LangChain types
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredFileLoader

# Google Drive
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Chroma
import chromadb

# === 공통 설정 ===
load_dotenv()
CHROMA_DB_PATH = "unified_chroma_db"
DEFAULT_COLLECTION_NAME = "unified_knowledge_db"
BATCH_SIZE = 5  # 배치 처리 크기

# === 공통: Upstage 임베딩 ===
class CustomUpstageEmbeddings:
    def __init__(self, model: str = "embedding-passage", chunk_size: int = 100):
        self.model = model
        self.chunk_size = chunk_size
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError(".env 파일에 UPSTAGE_API_KEY가 설정되지 않았습니다.")
        self.base_url = "https://api.upstage.ai/v1/embeddings"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts, self.model)

    def embed_query(self, text: str) -> List[float]:
        query_model = self.model.replace("passage", "query") if "passage" in self.model else self.model
        return self._embed([text], query_model)[0]

    def _embed(self, texts: List[str], model: str) -> List[List[float]]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        all_embeddings: List[List[float]] = []
        for i in range(0, len(texts), self.chunk_size):
            batch = texts[i:i + self.chunk_size]
            resp = requests.post(self.base_url, headers=headers, json={"input": batch, "model": model}, timeout=60)
            if resp.status_code != 200:
                raise RuntimeError(f"Upstage Embeddings API 오류: {resp.status_code} - {resp.text}")
            data = resp.json().get("data", [])
            # 응답의 index 순서를 보존하여 배치 순서대로 재배열
            batch_embeddings: List[Optional[List[float]]] = [None] * len(batch)
            for item in data:
                batch_embeddings[item["index"]] = item["embedding"]
            all_embeddings.extend([e for e in batch_embeddings if e is not None])
        return all_embeddings


# === 공통: Chroma 적재 ===
def add_to_chroma(documents: List[Document], collection_name: str) -> Tuple[int, int]:
    if not documents:
        return (0, 0)

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=collection_name)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = splitter.split_documents(documents)

    texts = [d.page_content for d in split_docs]
    metadatas = [d.metadata for d in split_docs]

    embeddings = CustomUpstageEmbeddings(model="embedding-passage")
    vectors = embeddings.embed_documents(texts)

    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_meta = metadatas[i:i + batch_size]
        batch_vecs = vectors[i:i + batch_size]
        batch_ids = [str(uuid.uuid4()) for _ in range(len(batch_texts))]
        collection.add(documents=batch_texts, metadatas=batch_meta, ids=batch_ids, embeddings=batch_vecs)

    return (len(split_docs), collection.count())


# === GDRIVE 수집 ===
def run_gdrive(folder_id: str, collection_name: str) -> int:
    print("=" * 50)
    print("Google Drive에서 데이터를 수집합니다...")
    creds = service_account.Credentials.from_service_account_file(
        "gdrive-credentials.json", scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=creds)

    parsed_cache_path = "parsed_cache.json"
    if os.path.exists(parsed_cache_path):
        with open(parsed_cache_path, "r", encoding="utf-8") as f:
            parsed_cache: Dict[str, str] = json.load(f)
    else:
        parsed_cache = {}

    batch_docs: List[Document] = []
    total_added = 0
    
    with tempfile.TemporaryDirectory() as temp_dir:
        def process_folder(fid: str) -> None:
            nonlocal batch_docs, total_added
            query = f"'{fid}' in parents"
            try:
                results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
                items = results.get("files", [])
            except Exception as e:
                print(f"  - 🚨 폴더 ID '{fid}' 접근 실패: {e}")
                print(f"  - ⏭️ 해당 폴더 건너뛰기")
                return

            for item in items:
                name = item["name"]
                file_id = item["id"]
                mime_type = item["mimeType"]
                print(f"  - 📄 파일 '{name}' (MIME: {mime_type})")
                
                # 폴더는 재귀 처리
                if mime_type == "application/vnd.google-apps.folder":
                    process_folder(file_id)
                    continue

                # 캐시 히트 확인
                if file_id in parsed_cache:
                    print(f"  - ⚡️ 캐시 히트! '{name}'는 이미 처리된 문서입니다.")
                    page_content = parsed_cache[file_id]
                    doc = Document(page_content=page_content, metadata={"source": name, "gdrive_file_id": file_id})
                    batch_docs.append(doc)
                else:
                    # content 변수 초기화
                    content: Optional[str] = None
                    
                    # 파일 확장자 확인
                    sanitized_file_name = name.replace("/", "_")
                    _, file_ext = os.path.splitext(sanitized_file_name)
                    ext = file_ext.lower()
                    
                    # 지원하는 확장자만 처리
                    if ext in ['.pdf', '.docx', '.pptx', '.xlsx', '.py', '.txt']:
                        # Google Workspace 파일인지 확인
                        if "google-apps" in mime_type:
                            # Google Workspace 파일은 Export API 사용
                            export_mime_types = {
                                "application/vnd.google-apps.document": "text/plain",
                                "application/vnd.google-apps.spreadsheet": "text/csv",
                                "application/vnd.google-apps.presentation": "text/plain",
                                "application/vnd.google-apps.drawing": "image/png",
                                "application/vnd.google-apps.form": "text/plain"
                            }
                            
                            export_mime = export_mime_types.get(mime_type)
                            if export_mime and mime_type != "application/vnd.google-apps.folder":
                                try:
                                    request = service.files().export_media(fileId=file_id, mimeType=export_mime)
                                    fh = io.BytesIO()
                                    downloader = MediaIoBaseDownload(fh, request)
                                    done = False
                                    while not done:
                                        status, done = downloader.next_chunk()
                                    
                                    if export_mime == "text/plain" or export_mime == "text/csv":
                                        content = fh.getvalue().decode('utf-8', errors='ignore')
                                        print(f"  - ✅ Google Workspace 파일 '{name}' Export 성공")
                                    else:
                                        # 이미지 등은 건너뛰기
                                        content = None
                                        print(f"  - ⏭️ 이미지 파일 '{name}' 건너뛰기")
                                except Exception as e:
                                    print(f"  - ⚠️ Google Workspace 파일 '{name}' Export 실패: {e}")
                                    content = None
                            elif mime_type == "application/vnd.google-apps.shortcut":
                                print(f"  - ⏭️ Google Workspace shortcut 파일 '{name}' 건너뛰기")
                                content = None
                            else:
                                print(f"  - ⏭️ 지원하지 않는 Google Workspace 파일 타입 '{name}' (MIME: {mime_type}) 건너뛰기")
                                content = None
                        else:
                            # 일반 파일은 기존 방식으로 다운로드
                            try:
                                request = service.files().get_media(fileId=file_id)
                                fh = io.BytesIO()
                                downloader = MediaIoBaseDownload(fh, request)
                                done = False
                                while not done:
                                    status, done = downloader.next_chunk()
                                
                                temp_file_path = os.path.join(temp_dir, sanitized_file_name)
                                with open(temp_file_path, "wb") as f:
                                    f.write(fh.getvalue())

                                # 파일 형식에 따라 처리
                                if ext in ['.pdf', '.docx', '.pptx', '.xlsx']:
                                    content = parse_with_upstage(temp_file_path, name)
                                    if content:
                                        print(f"  - ✅ 업스테이지 파서로 '{name}' 처리 성공")
                                    else:
                                        print(f"  - ⚠️ 업스테이지 파서로 '{name}' 처리 실패")
                                elif ext in ['.py', '.txt']:
                                    print(f"  - 📝 일반 텍스트 로더로 '{name}' 파일 처리 중...")
                                    try:
                                        loader = UnstructuredFileLoader(temp_file_path)
                                        loaded_docs = loader.load()
                                        if loaded_docs:
                                            content = loaded_docs[0].page_content
                                        print(f"  - ✅ '{name}' 처리 완료.")
                                    except Exception as e:
                                        print(f"  - ⚠️ 텍스트 파일 '{name}' 로드 실패: {e}")
                                        content = None
                            except Exception as e:
                                print(f"  - ⚠️ 파일 '{name}' 다운로드 실패: {e}")
                                content = None
                    else:
                        print(f"  - ⏭️ 지원하지 않는 파일 형식({ext})이므로 건너뛰기")

                    if content:
                        print(f"  - 💾 캐시에 '{name}'의 파싱 결과를 저장합니다.")
                        parsed_cache[file_id] = content
                        doc = Document(page_content=content, metadata={"source": name, "gdrive_file_id": file_id})
                        batch_docs.append(doc)

                # 배치 크기에 도달하면 즉시 처리
                if len(batch_docs) >= BATCH_SIZE:
                    print(f"\n💾 {len(batch_docs)}개의 문서를 배치로 처리합니다...")
                    added, total = add_to_chroma(batch_docs, collection_name)
                    total_added += added
                    print(f"  - ✅ 배치 처리 완료. 추가된 청크: {added}, 총 컬렉션 문서 수: {total}")
                    batch_docs = []

        process_folder(folder_id)

    # 남은 문서들 처리
    if batch_docs:
        print(f"\n💾 남은 {len(batch_docs)}개의 문서를 최종 처리합니다...")
        added, total = add_to_chroma(batch_docs, collection_name)
        total_added += added
        print(f"  - ✅ 최종 처리 완료. 추가된 청크: {added}, 총 컬렉션 문서 수: {total}")

    # 캐시 저장
    with open(parsed_cache_path, "w", encoding="utf-8") as f:
        json.dump(parsed_cache, f, ensure_ascii=False, indent=2)

    print(f"GDrive 총 추가된 청크 수: {total_added}")
    return total_added


def parse_with_upstage(file_path: str, original_file_name: str) -> Optional[str]:
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
            response = requests.post(url, headers=headers, files=files, data=data, timeout=120)
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


# === GitHub 수집 ===
def get_all_repos_from_org(org_name: str) -> List[Dict[str, Any]]:
    """조직의 모든 공개 리포지토리 목록을 가져옵니다."""
    repos = []
    page = 1
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    while True:
        url = f"https://api.github.com/orgs/{org_name}/repos?type=public&page={page}&per_page=100"
        try:
            response = requests.get(url, headers=headers, timeout=30)
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

def get_readme_content(repo_full_name: str) -> Optional[str]:
    """GitHub API를 통해 리포지토리의 README 파일 내용을 가져옵니다."""
    headers = {"Accept": "application/vnd.github.v3.raw"}
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    
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

def run_github(org_name: str, collection_name: str) -> int:
    print("=" * 50)
    print(f"GitHub 조직 '{org_name}'에서 README를 수집합니다...")
    
    # 캐시 파일 로드
    processed_cache_path = "processed_repos_cache.json"
    if os.path.exists(processed_cache_path):
        with open(processed_cache_path, "r", encoding="utf-8") as f:
            processed_repos = set(json.load(f))
        print(f"✅ 기존 캐시에서 {len(processed_repos)}개의 처리된 리포지토리 목록을 불러왔습니다.")
    else:
        processed_repos = set()

    total_added = 0

    try:
        print("=" * 50)
        print(f"🏢 {org_name} 조직의 리포지토리를 가져옵니다...")
        all_repos = get_all_repos_from_org(org_name)
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
                
                # 각 repo마다 개별적으로 처리 (옛 버전과 동일)
                added, total = add_to_chroma([doc], collection_name)
                total_added += added
                processed_repos.add(repo_name)
                print(f"  - ✅ '{repo_name}' 처리 완료. 추가된 청크: {added}")

            except Exception as e:
                print(f"  - 🚨 실패! '{repo_name}' 처리 중 예상치 못한 오류 발생: {e}")

    except Exception as e:
        print(f"\n🚨 스크립트 실행 중 치명적인 오류 발생: {e}")

    finally:
        print("=" * 50)
        print("최종 정리 및 저장을 수행합니다...")
        with open(processed_cache_path, "w", encoding="utf-8") as f:
            json.dump(list(processed_repos), f, ensure_ascii=False, indent=4)
        print(f"✅ 업데이트된 캐시를 '{processed_cache_path}'에 저장했습니다.")

    print(f"GitHub 총 추가된 청크 수: {total_added}")
    print("\n🎉 모든 작업이 완료되었습니다.")
    return total_added


# === Notion 수집 (완전한 블록 처리 로직) ===
def get_notion_page_ids():
    """환경 변수에서 모든 Notion 페이지 ID를 가져옵니다."""
    page_ids = []
    i = 1
    while True:
        page_id = os.getenv(f"NOTION_PAGE_ID_{i}")
        if page_id:
            # 페이지 ID에서 접두사 제거 및 형식 정규화
            if '-' in page_id:
                # 접두사-UUID 형태인 경우 UUID 부분만 추출
                parts = page_id.split('-')
                if len(parts) > 1 and len(parts[-1]) >= 32:
                    # 마지막 부분이 32자 이상이면 UUID로 간주
                    uuid_part = ''.join(parts[1:])  # 첫 번째 부분(접두사) 제거
                    page_id = uuid_part.replace('-', '')  # 하이픈 제거
            
            # 32자리 UUID인지 확인
            if len(page_id) == 32 and page_id.replace('-', '').isalnum():
                page_ids.append(page_id)
                print(f"✅ 페이지 ID {i} 정규화: {page_id}")
            else:
                print(f"⚠️ 잘못된 페이지 ID {i} 형식: {page_id}")
            i += 1
        else:
            break
    return page_ids

async def extract_rich_text(rich_text_list: List[Dict[str, Any]]) -> str:
    """Rich text 배열에서 텍스트를 추출합니다."""
    if not rich_text_list:
        return ""
    
    text_parts = []
    for rt in rich_text_list:
        text = rt.get("plain_text", "")
        annotations = rt.get("annotations", {})
        
        # 텍스트 스타일링 적용
        if annotations.get("bold"):
            text = f"**{text}**"
        if annotations.get("italic"):
            text = f"*{text}*"
        if annotations.get("strikethrough"):
            text = f"~~{text}~~"
        if annotations.get("underline"):
            text = f"__{text}__"
        if annotations.get("code"):
            text = f"`{text}`"
        
        # 링크 처리
        if rt.get("href"):
            text = f"[{text}]({rt['href']})"
        
        text_parts.append(text)
    
    return "".join(text_parts)

async def process_block_content(block: Dict[str, Any], headers: Dict[str, str]) -> List[str]:
    """블록의 내용을 처리하고 텍스트를 추출합니다."""
    content_parts = []
    block_type = block.get("type")
    block_data = block.get(block_type, {})
    
    # 기본 텍스트 블록들
    text_blocks = [
        "paragraph", "heading_1", "heading_2", "heading_3", 
        "bulleted_list_item", "numbered_list_item", "quote", "callout",
        "toggle", "to_do"
    ]
    
    if block_type in text_blocks and block_data.get("rich_text"):
        text = await extract_rich_text(block_data["rich_text"])
        if text.strip():
            # 블록 타입별 마크다운 포맷팅
            if block_type == "heading_1":
                content_parts.append(f"# {text}")
            elif block_type == "heading_2":
                content_parts.append(f"## {text}")
            elif block_type == "heading_3":
                content_parts.append(f"### {text}")
            elif block_type == "bulleted_list_item":
                content_parts.append(f"• {text}")
            elif block_type == "numbered_list_item":
                content_parts.append(f"1. {text}")
            elif block_type == "quote":
                content_parts.append(f"> {text}")
            elif block_type == "callout":
                icon = block_data.get("icon", {}).get("emoji", "💡")
                content_parts.append(f"{icon} **{text}**")
            elif block_type == "toggle":
                content_parts.append(f"<details><summary>{text}</summary>")
            elif block_type == "to_do":
                checked = block_data.get("checked", False)
                checkbox = "☑️" if checked else "☐"
                content_parts.append(f"{checkbox} {text}")
            else:
                content_parts.append(text)
    
    # 코드 블록
    elif block_type == "code":
        text = await extract_rich_text(block_data.get("rich_text", []))
        language = block_data.get("language", "")
        if text.strip():
            content_parts.append(f"```{language}\n{text}\n```")
    
    # 테이블
    elif block_type == "table":
        table_rows = block_data.get("table_rows", [])
        if table_rows:
            content_parts.append("| " + " | ".join([await extract_rich_text(cell.get("rich_text", [])) for cell in table_rows[0].get("cells", [])]) + " |")
            content_parts.append("| " + " | ".join(["---"] * len(table_rows[0].get("cells", []))) + " |")
            for row in table_rows[1:]:
                content_parts.append("| " + " | ".join([await extract_rich_text(cell.get("rich_text", [])) for cell in row.get("cells", [])]) + " |")
    
    # 이미지 - 임베딩에서 제외하고 메타데이터만 추가
    elif block_type == "image":
        image_data = block_data.get("image", {})
        caption = await extract_rich_text(image_data.get("caption", []))
        if caption.strip():
            content_parts.append(f"🖼️ **이미지**: {caption}")
        else:
            content_parts.append("🖼️ **이미지** (캡션 없음)")
    
    # 파일 - 임베딩에서 제외하고 메타데이터만 추가
    elif block_type == "file":
        file_data = block_data.get("file", {})
        caption = await extract_rich_text(file_data.get("caption", []))
        if caption.strip():
            content_parts.append(f"📎 **파일**: {caption}")
        else:
            content_parts.append("📎 **첨부 파일**")
    
    # 북마크 - 임베딩에서 제외하고 메타데이터만 추가
    elif block_type == "bookmark":
        url = block_data.get("url", "")
        caption = await extract_rich_text(block_data.get("caption", []))
        if caption.strip():
            content_parts.append(f"🔖 **북마크**: {caption}")
        else:
            content_parts.append(f"🔖 **북마크**: {url}")
    
    # 구분선
    elif block_type == "divider":
        content_parts.append("---")
    
    # 동기화된 블록 (재귀적 처리)
    elif block_type == "synced_block":
        synced_from = block_data.get("synced_from")
        if synced_from:
            # 동기화된 원본 블록의 내용을 가져옴
            try:
                synced_blocks = await get_block_children(synced_from.get("block_id"), headers)
                for synced_block in synced_blocks:
                    content_parts.extend(await process_block_content(synced_block, headers))
            except Exception as e:
                content_parts.append(f"⚠️ 동기화된 블록 로드 실패: {e}")
    
    # 하위 페이지
    elif block_type == "child_page":
        title = block_data.get("title", "")
        content_parts.append(f"📄 **{title}** (하위 페이지)")
    
    # 하위 데이터베이스
    elif block_type == "child_database":
        title = block_data.get("title", "")
        content_parts.append(f"🗃️ **{title}** (하위 데이터베이스)")
    
    # 목차
    elif block_type == "table_of_contents":
        content_parts.append("📑 **목차**")
    
    # 컬럼
    elif block_type == "column_list":
        # 컬럼은 하위 블록으로 처리됨
        pass
    
    # 컬럼
    elif block_type == "column":
        # 컬럼은 하위 블록으로 처리됨
        pass
    
    return content_parts

async def get_block_children(session: aiohttp.ClientSession, block_id: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """블록의 하위 블록들을 비동기로 가져옵니다."""
    all_blocks = []
    start_cursor = None
    
    while True:
        url = f"https://api.notion.com/v1/blocks/{block_id}/children"
        params = {"page_size": 100}
        if start_cursor:
            params["start_cursor"] = start_cursor
        
        try:
            async with session.get(url, headers=headers, params=params, timeout=30) as response:
                if response.status != 200:
                    print(f"  ❌ 블록 하위 요소 가져오기 실패: {response.status}")
                    break
                
                data = await response.json()
                blocks = data.get("results", [])
                all_blocks.extend(blocks)
                print(f"  📦 블록 {len(blocks)}개 로드됨 (총 {len(all_blocks)}개)")
                
                # 다음 페이지가 있는지 확인
                if not data.get("has_more"):
                    break
                
                start_cursor = data.get("next_cursor")
        
        except asyncio.TimeoutError:
            print(f"  ⏰ 블록 {block_id} 요청 시간 초과")
            break
        
        # API 레이트 리밋 방지
        await asyncio.sleep(0.05)
    
    return all_blocks

async def process_blocks_recursively(session: aiohttp.ClientSession, blocks: List[Dict[str, Any]], headers: Dict[str, str], depth: int = 0, max_depth: int = 10) -> List[str]:
    """블록들을 병렬로 처리하여 모든 내용을 추출합니다."""
    if depth > max_depth:
        print(f"  ⚠️ 최대 중첩 깊이({max_depth}) 도달, 재귀 중단")
        return []
    
    content_parts = []
    
    # 블록을 청크로 나누어 병렬 처리 (최대 5개씩)
    chunk_size = 5
    block_chunks = [blocks[i:i+chunk_size] for i in range(0, len(blocks), chunk_size)]
    
    for chunk_idx, chunk in enumerate(block_chunks):
        print(f"  {'  ' * depth}🔄 청크 {chunk_idx+1}/{len(block_chunks)} 병렬 처리 중... ({len(chunk)}개 블록)")
        
        # 청크 내 블록들을 병렬 처리
        tasks = []
        for block in chunk:
            tasks.append(process_single_block(session, block, headers, depth, max_depth))
        
        # 병렬 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  {'  ' * depth}❌ 블록 {i+1} 처리 실패: {result}")
            else:
                content_parts.extend(result)
    
    return content_parts

async def process_single_block(session: aiohttp.ClientSession, block: Dict[str, Any], headers: Dict[str, str], depth: int, max_depth: int) -> List[str]:
    """단일 블록을 처리합니다."""
    content_parts = []
    
    # 현재 블록의 내용 처리
    try:
        block_content = await process_block_content(block, headers)
        content_parts.extend(block_content)
    except Exception as e:
        print(f"  {'  ' * depth}❌ 블록 내용 처리 실패: {e}")
        return content_parts
    
    # 하위 블록이 있는지 확인 (재귀적 처리)
    if block.get("has_children", False) and depth < max_depth:
        try:
            child_blocks = await get_block_children(session, block["id"], headers)
            if child_blocks:
                child_content = await process_blocks_recursively(session, child_blocks, headers, depth + 1, max_depth)
                content_parts.extend(child_content)
        except Exception as e:
            print(f"  {'  ' * depth}⚠️ 하위 블록 로드 실패: {e}")
    
    return content_parts

async def load_notion_page_content(session: aiohttp.ClientSession, page_id: str, api_key: str) -> Document:
    """Notion API를 비동기로 호출하여 페이지 내용을 가져옵니다."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # 페이지 정보 가져오기
    page_url = f"https://api.notion.com/v1/pages/{page_id}"
    async with session.get(page_url, headers=headers, timeout=30) as page_response:
        if page_response.status != 200:
            raise Exception(f"페이지 정보 가져오기 실패: {page_response.status}")
        
        page_data = await page_response.json()
    
    # 페이지 제목 추출
    title = "제목 없음"
    if "properties" in page_data:
        for prop_name, prop_data in page_data["properties"].items():
            if prop_data.get("type") == "title" and prop_data.get("title"):
                title = await extract_rich_text(prop_data["title"])
                break
    
    # 페이지의 모든 블록을 재귀적으로 가져오기
    print(f"  🔍 페이지 블록 탐색 중...")
    blocks = await get_block_children(session, page_id, headers)
    
    # 모든 블록을 병렬로 처리
    print(f"  📝 {len(blocks)}개 블록 병렬 처리 중...")
    content_parts = await process_blocks_recursively(session, blocks, headers)
    
    content = "\n\n".join(content_parts)
    
    # Document 객체 생성
    doc = Document(
        page_content=content,
        metadata={
            "title": title,
            "source": f"notion_page_{page_id}",
            "page_id": page_id,
            "block_count": len(blocks)
        }
    )
    
    return doc

async def load_all_notion_pages(page_ids: List[str], api_key: str) -> List[Document]:
    """모든 Notion 페이지를 병렬로 로드합니다."""
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for i, page_id in enumerate(page_ids, 1):
            print(f"📄 페이지 {i}/{len(page_ids)} 병렬 로드 준비... (ID: {page_id})")
            tasks.append(load_single_page_with_logging(session, page_id, api_key, i, len(page_ids)))
        
        print(f"🚀 {len(tasks)}개 페이지를 병렬로 로드 시작...")
        start_time = time.time()
        
        # 모든 페이지를 병렬로 로드
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        print(f"⏱️ 병렬 로드 완료: {end_time - start_time:.2f}초")
        
        # 성공한 결과만 필터링
        notion_docs = []
        for i, result in enumerate(results, 1):
            if isinstance(result, Exception):
                print(f"❌ 페이지 {i} 로드 실패: {result}")
            else:
                notion_docs.append(result)
        
        return notion_docs

async def load_single_page_with_logging(session: aiohttp.ClientSession, page_id: str, api_key: str, page_num: int, total_pages: int) -> Document:
    """단일 페이지를 로드하고 로깅합니다."""
    try:
        print(f"\n📄 페이지 {page_num}/{total_pages} 로드 시작... (ID: {page_id})")
        
        doc = await load_notion_page_content(session, page_id, api_key)
        
        print(f"✅ 페이지 {page_num} 로드 완료!")
        print(f"  - 📄 {doc.metadata.get('title', '제목 없음')}")
        print(f"  - 📊 블록 수: {doc.metadata.get('block_count', 0)}개")
        print(f"  - 📝 텍스트 길이: {len(doc.page_content)}자")
        
        return doc
        
    except Exception as e:
        print(f"❌ 페이지 {page_num} (ID: {page_id}) 로드 실패: {e}")
        raise e

def run_notion(collection_name: str) -> int:
    # 환경변수에서 Notion 페이지 ID들 로드 (NOTION_PAGE_ID_1 ...)
    page_ids = get_notion_page_ids()

    if not page_ids:
        print("⚠️ 설정된 Notion 페이지 ID가 없습니다. NOTION_PAGE_ID_1,2,... 환경변수를 설정하세요.")
        return 0

    api_key = os.getenv("NOTION_API_KEY")
    if not api_key:
        print("⚠️ NOTION_API_KEY가 설정되지 않았습니다.")
        return 0

    docs = asyncio.run(load_all_notion_pages(page_ids, api_key))
    added, total = add_to_chroma(docs, collection_name)
    print(f"Notion 문서 {len(docs)}개 → 청크 {added}개 추가. 컬렉션 문서 수: {total}")
    return added


# === 엔트리포인트 ===
def main():
    parser = argparse.ArgumentParser(description="GDrive/GitHub/Notion 데이터를 unified_chroma_db로 적재하는 통합 스크립트")
    parser.add_argument("--source", choices=["gdrive", "github", "notion", "all"], required=True, help="데이터 소스 선택")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION_NAME, help="ChromaDB 컬렉션 이름")
    parser.add_argument("--gdrive_folder_id", default=os.getenv("GDRIVE_FOLDER_ID", ""), help="Google Drive 폴더 ID(소스=gdrive 또는 all)")
    parser.add_argument("--github_org", default=os.getenv("ORG_NAME", "YBIGTA"), help="GitHub Org 이름(소스=github 또는 all)")
    args = parser.parse_args()

    collection_name = args.collection

    total_added = 0

    if args.source in ("gdrive", "all"):
        if not args.gdrive_folder_id:
            print("⚠️ GDrive 폴더 ID가 비어있어 건너뜁니다. --gdrive_folder_id 또는 GDRIVE_FOLDER_ID 설정 필요")
        else:
            total_added += run_gdrive(args.gdrive_folder_id, collection_name)

    if args.source in ("github", "all"):
        total_added += run_github(args.github_org, collection_name)

    if args.source in ("notion", "all"):
        total_added += run_notion(collection_name)

    print("=" * 50)
    print(f"🎉 통합 작업 완료. 총 추가된 청크 수(대략): {total_added}")


if __name__ == "__main__":
    main() 