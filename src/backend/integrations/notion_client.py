"""
Notion API 클라이언트
Notion 페이지 및 데이터베이스와의 통합을 담당
"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Any
from langchain_core.documents import Document


class NotionClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

    def get_page_ids_from_env(self) -> List[str]:
        """환경 변수에서 모든 Notion 페이지 ID를 가져옵니다."""
        page_ids = []
        i = 1
        while True:
            page_id = os.getenv(f"NOTION_PAGE_ID_{i}")
            if page_id:
                # 페이지 ID 정규화
                if '-' in page_id:
                    parts = page_id.split('-')
                    if len(parts) > 1 and len(parts[-1]) >= 32:
                        uuid_part = ''.join(parts[1:])
                        page_id = uuid_part.replace('-', '')
                
                if len(page_id) == 32 and page_id.replace('-', '').isalnum():
                    page_ids.append(page_id)
                i += 1
            else:
                break
        return page_ids

    async def get_block_children(self, session: aiohttp.ClientSession, block_id: str, timeout: int = 30) -> List[Dict[str, Any]]:
        """블록의 하위 블록들을 비동기로 가져옵니다."""
        all_blocks = []
        start_cursor = None
        
        while True:
            url = f"{self.base_url}/blocks/{block_id}/children"
            params = {"page_size": 100}
            if start_cursor:
                params["start_cursor"] = start_cursor
            
            try:
                async with session.get(url, headers=self.headers, params=params, timeout=timeout) as response:
                    if response.status != 200:
                        break
                    
                    data = await response.json()
                    blocks = data.get("results", [])
                    all_blocks.extend(blocks)
                    
                    if not data.get("has_more"):
                        break
                    
                    start_cursor = data.get("next_cursor")
            
            except asyncio.TimeoutError:
                break
            
            await asyncio.sleep(0.05)  # Rate limit protection
        
        return all_blocks

    def extract_rich_text(self, rich_text_list: List[Dict[str, Any]]) -> str:
        """Rich text 배열에서 텍스트를 추출합니다."""
        if not rich_text_list:
            return ""
        
        text_parts = []
        for rt in rich_text_list:
            text = rt.get("plain_text", "")
            text_parts.append(text)
        
        return "".join(text_parts)

    def process_block_content(self, block: Dict[str, Any]) -> List[str]:
        """블록의 내용을 처리하고 텍스트를 추출합니다."""
        content_parts = []
        block_type = block.get("type")
        block_data = block.get(block_type, {})
        
        # 텍스트 블록 처리
        text_blocks = ["paragraph", "heading_1", "heading_2", "heading_3", 
                      "bulleted_list_item", "numbered_list_item", "quote", "code"]
        
        if block_type in text_blocks and block_data.get("rich_text"):
            text = self.extract_rich_text(block_data["rich_text"])
            if text.strip():
                if block_type.startswith("heading"):
                    level = block_type.split("_")[1]
                    text = "#" * int(level) + " " + text
                elif block_type == "bulleted_list_item":
                    text = "• " + text
                elif block_type == "numbered_list_item":
                    text = "1. " + text
                elif block_type == "quote":
                    text = "> " + text
                elif block_type == "code":
                    text = f"```\\n{text}\\n```"
                
                content_parts.append(text)
        
        return content_parts

    async def get_page_metadata(self, session: aiohttp.ClientSession, page_id: str) -> Dict[str, Any]:
        """페이지의 메타데이터를 가져옵니다."""
        try:
            async with session.get(
                f"{self.base_url}/pages/{page_id}",
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    page_data = await response.json()
                    return {
                        'last_edited_time': page_data.get('last_edited_time'),
                        'created_time': page_data.get('created_time'),
                        'properties': page_data.get('properties', {})
                    }
        except Exception as e:
            print(f"⚠️ 페이지 메타데이터 가져오기 실패 {page_id}: {e}")
        return {}

    async def load_page_content(self, session: aiohttp.ClientSession, page_id: str) -> Document:
        """Notion 페이지 내용을 비동기로 로드합니다."""
        # 페이지 정보 가져오기
        page_url = f"{self.base_url}/pages/{page_id}"
        async with session.get(page_url, headers=self.headers, timeout=30) as response:
            if response.status != 200:
                raise Exception(f"페이지 정보 가져오기 실패: {response.status}")
            
            page_data = await response.json()
        
        # 페이지 제목 추출
        title = "제목 없음"
        if "properties" in page_data:
            for prop_name, prop_data in page_data["properties"].items():
                if prop_data.get("type") == "title" and prop_data.get("title"):
                    title = self.extract_rich_text(prop_data["title"])
                    break
        
        # 페이지 블록 가져오기
        blocks = await self.get_block_children(session, page_id)
        
        # 블록 내용 처리
        content_parts = []
        for block in blocks:
            content_parts.extend(self.process_block_content(block))
        
        content = "\\n\\n".join(content_parts)
        
        # Document 객체 생성
        # 페이지 메타데이터 가져오기
        page_metadata = await self.get_page_metadata(session, page_id)
        
        doc = Document(
            page_content=content,
            metadata={
                "title": title,
                "source": "notion",
                "page_id": page_id,
                "block_count": len(blocks),
                "last_modified": page_metadata.get('last_edited_time', ''),
                "created_time": page_metadata.get('created_time', '')
            }
        )
        
        return doc

    async def load_all_pages(self, check_updates: bool = True) -> List[Document]:
        """모든 Notion 페이지를 병렬로 로드합니다. 
        
        Args:
            check_updates: True면 페이지 업데이트 상태를 확인합니다.
        """
        page_ids = self.get_page_ids_from_env()
        
        if not page_ids:
            print("⚠️ 설정된 Notion 페이지 ID가 없습니다.")
            return []
        
        print(f"🔍 총 {len(page_ids)}개의 Notion 페이지를 발견했습니다.")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i, page_id in enumerate(page_ids, 1):
                print(f"📄 페이지 {i}/{len(page_ids)} 로드 준비... (ID: {page_id})")
                tasks.append(self.load_page_content(session, page_id))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            docs = []
            for i, result in enumerate(results, 1):
                if isinstance(result, Exception):
                    print(f"❌ 페이지 {i} 로드 실패: {result}")
                else:
                    print(f"✅ 페이지 {i} 로드 완료: {result.metadata.get('title', '제목 없음')}")
                    docs.append(result)
            
            return docs