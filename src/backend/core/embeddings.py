"""
임베딩 모델 관리
Upstage API를 사용한 임베딩 생성 (langchain-upstage 패키지 사용)
"""

import os
import asyncio
import itertools
from typing import List
from langchain_core.embeddings import Embeddings

try:
    from langchain_upstage import UpstageEmbeddings
except ImportError:
    print("⚠️ langchain-upstage 패키지가 설치되지 않았습니다. pip install langchain-upstage를 실행해주세요.")
    UpstageEmbeddings = None


class AsyncUpstageEmbeddings(Embeddings):
    """langchain-upstage를 사용한 Upstage 임베딩 클래스 (다중 API 키 로드 밸런싱)"""
    
    def __init__(self, model: str = "embedding-query"):
        if not UpstageEmbeddings:
            raise ImportError("langchain-upstage 패키지가 필요합니다. pip install langchain-upstage를 실행해주세요.")
        
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
        self.key_cycle = itertools.cycle(self.api_keys)
        
        # langchain-upstage 임베딩 인스턴스들 (각 API 키별로)
        self.embedders = []
        for api_key in self.api_keys:
            embedder = UpstageEmbeddings(api_key=api_key, model=model)
            self.embedders.append(embedder)
        self.embedder_cycle = itertools.cycle(self.embedders)
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서들을 병렬로 임베딩합니다."""
        try:
            # langchain-upstage를 사용하여 임베딩 (로드 밸런싱)
            embedder = next(self.embedder_cycle)
            embeddings = await asyncio.to_thread(embedder.embed_documents, texts)
            
            # 4096 차원 확인
            if embeddings and len(embeddings[0]) != 4096:
                print(f"⚠️ 예상치 못한 임베딩 차원: {len(embeddings[0])}, 4096 차원 예상")
            
            return embeddings
            
        except Exception as e:
            print(f"⚠️ 임베딩 실패: {e}")
            # 실패시 기본값으로 대체 (4096 차원)
            return [[0.0] * 4096 for _ in texts]
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """동기 인터페이스 (LangChain 호환성)"""
        try:
            # 기존 이벤트 루프가 실행 중인지 확인
            loop = asyncio.get_running_loop()
            # 이미 이벤트 루프가 실행 중이면 새 스레드에서 실행
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.aembed_documents(texts))
                return future.result()
        except RuntimeError:
            # 이벤트 루프가 실행 중이 아니면 일반적인 방식으로 실행
            return asyncio.run(self.aembed_documents(texts))
    
    async def aembed_query(self, text: str) -> List[float]:
        """쿼리를 임베딩합니다."""
        try:
            # langchain-upstage를 사용하여 임베딩 (로드 밸런싱)
            embedder = next(self.embedder_cycle)
            embedding = await asyncio.to_thread(embedder.embed_query, text)
            
            # 4096 차원 확인
            if len(embedding) != 4096:
                print(f"⚠️ 예상치 못한 임베딩 차원: {len(embedding)}, 4096 차원 예상")
            
            return embedding
            
        except Exception as e:
            print(f"⚠️ 쿼리 임베딩 실패: {e}")
            # 실패시 기본값으로 대체 (4096 차원)
            return [0.0] * 4096
    
    def embed_query(self, text: str) -> List[float]:
        """동기 인터페이스 (LangChain 호환성)"""
        try:
            # 기존 이벤트 루프가 실행 중인지 확인
            loop = asyncio.get_running_loop()
            # 이미 이벤트 루프가 실행 중이면 새 스레드에서 실행
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.aembed_query(text))
                return future.result()
        except RuntimeError:
            # 이벤트 루프가 실행 중이 아니면 일반적인 방식으로 실행
            return asyncio.run(self.aembed_query(text))


class SyncUpstageEmbeddings(Embeddings):
    """langchain-upstage를 사용한 동기 Upstage 임베딩 클래스"""
    
    def __init__(self, model: str = "embedding-passage"):
        if not UpstageEmbeddings:
            raise ImportError("langchain-upstage 패키지가 필요합니다. pip install langchain-upstage를 실행해주세요.")
            
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")
            
        self.model = model
        self.embedder = UpstageEmbeddings(api_key=self.api_key, model=model)
        
        # 쿼리용 임베더도 준비
        query_model = model.replace("passage", "query") if "passage" in model else "embedding-query"
        self.query_embedder = UpstageEmbeddings(api_key=self.api_key, model=query_model)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서들을 임베딩합니다."""
        try:
            embeddings = self.embedder.embed_documents(texts)
            
            # 4096 차원 확인
            if embeddings and len(embeddings[0]) != 4096:
                print(f"⚠️ 예상치 못한 임베딩 차원: {len(embeddings[0])}, 4096 차원 예상")
                
            return embeddings
            
        except Exception as e:
            print(f"⚠️ 문서 임베딩 실패: {e}")
            # 실패시 기본값으로 대체 (4096 차원)
            return [[0.0] * 4096 for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """쿼리를 임베딩합니다."""
        try:
            embedding = self.query_embedder.embed_query(text)
            
            # 4096 차원 확인
            if len(embedding) != 4096:
                print(f"⚠️ 예상치 못한 임베딩 차원: {len(embedding)}, 4096 차원 예상")
                
            return embedding
            
        except Exception as e:
            print(f"⚠️ 쿼리 임베딩 실패: {e}")
            # 실패시 기본값으로 대체 (4096 차원)
            return [0.0] * 4096