# src/backend/nlp/semantic_search.py

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SemanticSearchEngine:
    def __init__(self, chroma_manager=None, embedding_client=None):
        self.chroma_manager = chroma_manager
        self.embedding_client = embedding_client

    async def search(self,
                    query: str,
                    filters: Optional[Dict[str, Any]] = None,
                    top_k: int = 10,
                    sources: Optional[List[str]] = None) -> Dict[str, Any]:
        try:
            if not self.chroma_manager:
                logger.warning("ChromaDB 매니저가 설정되지 않았습니다.")
                return {"documents": [], "scores": [], "metadata": []}

            # 1. 쿼리 임베딩 생성 (실제 API 호출)
            query_embedding = await self._get_query_embedding(query)
            if query_embedding is None:
                return {"documents": [], "scores": [], "metadata": []}

            # 2. ChromaDB에서 검색 (실제 DB 검색)
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
            # 실제 임베딩 API 호출
            if hasattr(self.embedding_client, 'embed_query'):
                # AsyncUpstageEmbeddings 클래스 사용
                embedding = await self.embedding_client.embed_query(query)
                logger.debug(f"임베딩 생성 성공: {len(embedding)} 차원")
                return embedding
            elif hasattr(self.embedding_client, 'embed_documents'):
                # LangChain 스타일 임베딩 클라이언트
                embeddings = self.embedding_client.embed_documents([query])
                if embeddings and len(embeddings) > 0:
                    logger.debug(f"임베딩 생성 성공: {len(embeddings[0])} 차원")
                    return embeddings[0]
            else:
                logger.error("지원되지 않는 임베딩 클라이언트 타입입니다.")
                return None
                
        except Exception as e:
            logger.error(f"쿼리 임베딩 생성 실패: {str(e)}")
            return None

    async def _search_in_chroma(self, query: str, query_embedding: List[float], 
                               filters: Optional[Dict], top_k: int, 
                               sources: Optional[List[str]]) -> Dict[str, Any]:
        """ChromaDB에서 검색"""
        try:
            if not self.chroma_manager:
                logger.warning("ChromaDB 매니저가 설정되지 않았습니다.")
                return {"documents": [], "scores": [], "metadata": []}

            # ChromaIndexManager의 실제 메서드 사용
            results = self.chroma_manager.vector_search(
                query=query,
                top_k=top_k,
                filter=filters
            )
            
            # 결과 형식 변환
            documents = []
            scores = []
            metadata = []
            
            for result in results:
                if isinstance(result, dict):
                    # ChromaIndexManager에서 반환하는 형식
                    documents.append(result.get('content', ''))
                    scores.append(result.get('score', 0.0))
                    metadata.append(result.get('metadata', {}))
                else:
                    # 다른 형식의 결과 처리
                    logger.warning(f"예상치 못한 결과 형식: {type(result)}")
                    continue
            
            logger.debug(f"ChromaDB 검색 완료: {len(documents)}개 결과")
            
            return {
                "documents": documents,
                "scores": scores,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"ChromaDB 검색 오류: {str(e)}")
            return {"documents": [], "scores": [], "metadata": []}

    def get_search_stats(self) -> Dict[str, Any]:
        """검색 통계 반환"""
        return {
            "engine_type": "semantic_search",
            "chroma_available": self.chroma_manager is not None,
            "embedding_available": self.embedding_client is not None,
            "supported_features": [
                "vector_similarity_search",
                "embedding_generation",
                "metadata_filtering",
                "top_k_ranking"
            ]
        }