
import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List, Dict, Any, Optional
from openai import OpenAI
import itertools
import time

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()
all_docs = []

# Upstage API 키 풀 설정 (로드 밸런싱용)
UPSTAGE_API_KEYS = []
for i in range(1, 9):  # UPSTAGE_API_KEY1 ~ UPSTAGE_API_KEY8
    key = os.getenv(f"UPSTAGE_API_KEY{i}")
    if key:
        UPSTAGE_API_KEYS.append(key)

print(f"🔑 {len(UPSTAGE_API_KEYS)}개의 Upstage API 키를 발견했습니다.")

# API 키 순환을 위한 이터레이터
api_key_cycle = itertools.cycle(UPSTAGE_API_KEYS) if UPSTAGE_API_KEYS else itertools.cycle([os.getenv("UPSTAGE_API_KEY")])

# 커스텀 Upstage 임베딩 클래스 (비동기)
class AsyncUpstageEmbeddings:
    def __init__(self, api_keys: List[str], model="embedding-query"):
        self.api_keys = api_keys
        self.model = model
        self.base_url = "https://api.upstage.ai/v1"
        self.key_cycle = itertools.cycle(api_keys) if api_keys else itertools.cycle([os.getenv("UPSTAGE_API_KEY")])
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서들을 병렬로 임베딩합니다."""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for text in texts:
                api_key = next(self.key_cycle)
                tasks.append(self._embed_single(session, text, api_key))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            embeddings = []
            for result in results:
                if isinstance(result, Exception):
                    print(f"⚠️ 임베딩 실패: {result}")
                    # 실패시 기본값으로 대체
                    embeddings.append([0.0] * 4096)
                else:
                    embeddings.append(result)
            
            return embeddings
    
    async def _embed_single(self, session: aiohttp.ClientSession, text: str, api_key: str) -> List[float]:
        """단일 텍스트를 임베딩합니다."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "input": text,
            "model": self.model
        }
        
        url = f"{self.base_url}/embeddings"
        async with session.post(url, headers=headers, json=data, timeout=30) as response:
            if response.status == 200:
                result = await response.json()
                return result["data"][0]["embedding"]
            else:
                raise Exception(f"임베딩 API 호출 실패: {response.status}")
    
    def embed_query(self, text: str) -> List[float]:
        """쿼리를 임베딩합니다 (동기)."""
        return asyncio.run(self._embed_single_sync(text))
    
    async def _embed_single_sync(self, text: str) -> List[float]:
        async with aiohttp.ClientSession() as session:
            api_key = next(self.key_cycle)
            return await self._embed_single(session, text, api_key)

# Upstage 임베딩 인스턴스 생성
embeddings = AsyncUpstageEmbeddings(UPSTAGE_API_KEYS)

# --- 1. Notion 페이지 데이터 로드 ---
print("="*50)
print("Phase 1: Notion 페이지에서 데이터를 불러오는 중입니다...")

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

def extract_rich_text(rich_text_list: List[Dict[str, Any]]) -> str:
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

def process_block_content(block: Dict[str, Any], headers: Dict[str, str]) -> List[str]:
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
        text = extract_rich_text(block_data["rich_text"])
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
        text = extract_rich_text(block_data.get("rich_text", []))
        language = block_data.get("language", "")
        if text.strip():
            content_parts.append(f"```{language}\n{text}\n```")
    
    # 테이블
    elif block_type == "table":
        table_rows = block_data.get("table_rows", [])
        if table_rows:
            content_parts.append("| " + " | ".join([extract_rich_text(cell.get("rich_text", [])) for cell in table_rows[0].get("cells", [])]) + " |")
            content_parts.append("| " + " | ".join(["---"] * len(table_rows[0].get("cells", []))) + " |")
            for row in table_rows[1:]:
                content_parts.append("| " + " | ".join([extract_rich_text(cell.get("rich_text", [])) for cell in row.get("cells", [])]) + " |")
    
    # 이미지 - 임베딩에서 제외하고 메타데이터만 추가
    elif block_type == "image":
        image_data = block_data.get("image", {})
        caption = extract_rich_text(image_data.get("caption", []))
        if caption.strip():
            content_parts.append(f"🖼️ **이미지**: {caption}")
        else:
            content_parts.append("🖼️ **이미지** (캡션 없음)")
    
    # 파일 - 임베딩에서 제외하고 메타데이터만 추가
    elif block_type == "file":
        file_data = block_data.get("file", {})
        caption = extract_rich_text(file_data.get("caption", []))
        if caption.strip():
            content_parts.append(f"📎 **파일**: {caption}")
        else:
            content_parts.append("📎 **첨부 파일**")
    
    # 북마크 - 임베딩에서 제외하고 메타데이터만 추가
    elif block_type == "bookmark":
        url = block_data.get("url", "")
        caption = extract_rich_text(block_data.get("caption", []))
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
                synced_blocks = get_block_children(synced_from.get("block_id"), headers)
                for synced_block in synced_blocks:
                    content_parts.extend(process_block_content(synced_block, headers))
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
        block_content = process_block_content(block, headers)
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
                title = extract_rich_text(prop_data["title"])
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

# Notion 페이지 ID 목록 (동적으로 환경 변수에서 가져옴)
NOTION_PAGE_IDS = get_notion_page_ids()

if not NOTION_PAGE_IDS:
    print("⚠️ 설정된 Notion 페이지 ID가 없습니다.")
    print("   .env 파일에 NOTION_PAGE_ID_1, NOTION_PAGE_ID_2 등을 추가해주세요.")
else:
    print(f"🔍 총 {len(NOTION_PAGE_IDS)}개의 Notion 페이지를 발견했습니다.")

async def load_all_notion_pages(page_ids: List[str], api_key: str) -> List[Document]:
    """모든 Notion 페이지를 병렬로 로드합니다."""
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

# Notion 페이지들을 병렬로 로드
notion_docs = asyncio.run(load_all_notion_pages(NOTION_PAGE_IDS, os.getenv("NOTION_API_KEY")))

all_docs.extend(notion_docs)
print(f"\n✅ 총 {len(notion_docs)}개의 Notion 문서를 불러왔습니다.")

# --- 2. 최종 DB 생성 ---
print("="*50)
if all_docs:
    print(f"Phase 2: 총 {len(all_docs)}개의 문서를 기반으로 DB를 생성합니다.")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(all_docs)

    # Upstage 임베딩을 사용하여 벡터 DB 생성 (병렬 처리)
    print(f"🔗 {len(UPSTAGE_API_KEYS)}개의 Upstage API 키를 사용하여 병렬 임베딩 생성...")
    
    # 문서 텍스트 추출
    text_contents = [doc.page_content for doc in texts]
    
    # 병렬 임베딩 생성
    start_time = time.time()
    embeddings_list = asyncio.run(embeddings.embed_documents(text_contents))
    end_time = time.time()
    print(f"⚡ 임베딩 생성 완료: {end_time - start_time:.2f}초 ({len(embeddings_list)}개 벡터)")
    
    # FAISS 벡터스토어 생성
    vectorstore = FAISS.from_embeddings(
        list(zip(text_contents, embeddings_list)),
        embedding=embeddings,
        metadatas=[doc.metadata for doc in texts]
    )
    vectorstore.save_local("notion_faiss_index")
    print("\n🎉 모든 데이터를 기반으로 Vector DB가 성공적으로 저장되었습니다.")
else:
    print("\n⚠️ 로드된 문서가 없어 DB를 생성하지 않았습니다.")