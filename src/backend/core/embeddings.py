"""
임베딩 모델 관리
Upstage API를 사용한 임베딩 생성 (다중 API 키 지원)
"""

import os
import asyncio
import aiohttp
import itertools
from typing import List
from langchain_core.embeddings import Embeddings


class AsyncUpstageEmbeddings(Embeddings):
    """비동기 Upstage 임베딩 클래스 (다중 API 키 로드 밸런싱)"""
    
    def __init__(self, model: str = "embedding-query"):
        # API 키 풀 설정
        self.api_keys = []
        for i in range(1, 9):  # UPSTAGE_API_KEY1 ~ UPSTAGE_API_KEY8
            key = os.getenv(f"UPSTAGE_API_KEY{i}")
            if key:
                self.api_keys.append(key)
        
        # 단일 키 폴백
        if not self.api_keys:
            single_key = os.getenv("UPSTAGE_API_KEY")
            if single_key:
                self.api_keys = [single_key]
            else:
                raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")
        
        self.model = model
        self.base_url = "https://api.upstage.ai/v1"
        self.key_cycle = itertools.cycle(self.api_keys)
    
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
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
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
                    # 실패시 기본값으로 대체 (임베딩 차원에 맞춰 조정 필요)
                    embeddings.append([0.0] * 4096)
                else:
                    embeddings.append(result)
            
            return embeddings
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """동기 인터페이스 (LangChain 호환성)"""
        try:
            # 기존 이벤트 루프가 실행 중인지 확인
            loop = asyncio.get_running_loop()
            # 이미 이벤트 루프가 실행 중이면 새 스레드에서 실행
            import concurrent.futures
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(self.aembed_documents(texts))
        except RuntimeError:
            # 이벤트 루프가 실행 중이 아니면 일반적인 방식으로 실행
            return asyncio.run(self.aembed_documents(texts))
    
    async def aembed_query(self, text: str) -> List[float]:
        """쿼리를 임베딩합니다."""
        async with aiohttp.ClientSession() as session:
            api_key = next(self.key_cycle)
            return await self._embed_single(session, text, api_key)
    
    def embed_query(self, text: str) -> List[float]:
        """동기 인터페이스 (LangChain 호환성)"""
        try:
            # 기존 이벤트 루프가 실행 중인지 확인
            loop = asyncio.get_running_loop()
            # 이미 이벤트 루프가 실행 중이면 새 스레드에서 실행
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(self.aembed_query(text))
        except RuntimeError:
            # 이벤트 루프가 실행 중이 아니면 일반적인 방식으로 실행
            return asyncio.run(self.aembed_query(text))


class SyncUpstageEmbeddings(Embeddings):
    """동기 Upstage 임베딩 클래스 (단일 API 키)"""
    
    def __init__(self, model: str = "embedding-passage"):
        self.model = model
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")
        self.base_url = "https://api.upstage.ai/v1/embeddings"
    
    def _embed(self, texts: List[str]) -> List[List[float]]:
        """텍스트 리스트를 임베딩합니다."""
        import requests
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {"input": texts, "model": self.model}
        
        response = requests.post(self.base_url, headers=headers, json=data)
        
        if response.status_code == 200:
            response_data = response.json().get("data", [])
            embeddings = [None] * len(texts)
            for item in response_data:
                embeddings[item['index']] = item['embedding']
            return embeddings
        else:
            raise Exception(f"Upstage Embeddings API 오류: {response.status_code}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서들을 임베딩합니다."""
        return self._embed(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """쿼리를 임베딩합니다."""
        # 쿼리용 모델로 전환
        query_model = self.model.replace("passage", "query")
        temp_model = self.model
        self.model = query_model
        
        embedding = self._embed([text])[0]
        
        # 원래 모델로 복원
        self.model = temp_model
        return embedding