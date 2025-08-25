"""
의미적 검색 엔진 (SemanticSearchEngine)

FAISS 기반 벡터 검색을 제공합니다.
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """FAISS 기반 의미적 검색 엔진"""
    
    def __init__(self, chroma_manager=None, embedding_client=None):
        self.chroma_manager = chroma_manager
        self.embedding_client = embedding_client
    
    async def search(self, 
                    query: str, 
                    filters: Optional[Dict[str, Any]] = None, 
                    top_k: int = 10, 
                    sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        의미적 검색 실행
        
        Args:
            query: 검색 쿼리
            filters: 검색 필터
            top_k: 반환할 결과 수
            sources: 검색할 소스 목록
            
        Returns:
            검색 결과
        """
        try:
            if not self.chroma_manager:
                logger.warning("ChromaDB 매니저가 설정되지 않았습니다.")
                return {"documents": [], "scores": [], "metadata": []}
            
            # 쿼리 임베딩 생성
            query_embedding = await self._get_query_embedding(query)
            if query_embedding is None:
                return {"documents": [], "scores": [], "metadata": []}
            
            # ChromaDB에서 검색
            results = await self._search_in_chroma(query, query_embedding, filters, top_k, sources)
            
            return results
            
        except Exception as e:
            logger.error(f"의미적 검색 오류: {str(e)}")
            return {"documents": [], "scores": [], "metadata": []}
    
    async def _get_query_embedding(self, query: str) -> Optional[List[float]]:
        """쿼리 임베딩 생성"""
        
        if not self.embedding_client:
            logger.warning("임베딩 클라이언트가 설정되지 않았습니다.")
            return None
        
        try:
            # Upstage 임베딩 클라이언트 사용 (4096차원)
            if hasattr(self.embedding_client, 'embed_query'):
                embedding = self.embedding_client.embed_query(query)
            else:
                embedding = await self.embedding_client.aembed_query(query)
            
            return embedding
            
        except Exception as e:
            logger.error(f"쿼리 임베딩 생성 실패: {str(e)}")
            return None
    
    async def _search_in_chroma(self, 
                               query: str, 
                               query_embedding: List[float], 
                               filters: Optional[Dict], 
                               top_k: int, 
                               sources: Optional[List[str]]) -> Dict[str, Any]:
        """ChromaDB에서 검색"""
        
        try:
            # HybridChromaManager를 통한 검색 (Upstage 4096차원 임베딩 사용)
            if hasattr(self.chroma_manager, 'vector_search'):
                search_results = self.chroma_manager.vector_search(
                    query=query,
                    query_embedding=query_embedding,
                    top_k=top_k,
                    filter=filters
                )
                
                # 결과를 표준 형식으로 변환
                documents = []
                scores = []
                metadata = []
                
                for result in search_results:
                    documents.append(result.get('content', ''))
                    scores.append(result.get('score', 0.0))
                    metadata.append(result.get('metadata', {}))
                
                return {
                    "documents": documents,
                    "scores": scores,
                    "metadata": metadata
                }
            else:
                logger.warning("ChromaDB 매니저에 vector_search 메소드가 없습니다.")
                return {"documents": [], "scores": [], "metadata": []}
            
        except Exception as e:
            logger.error(f"ChromaDB 검색 오류: {str(e)}")
            return {"documents": [], "scores": [], "metadata": []}