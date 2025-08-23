"""
하이브리드 검색 시스템 (HybridRetriever)

FAISS 벡터 검색과 키워드 검색을 결합하여 최적의 검색 결과를 제공합니다.
RRF(Reciprocal Rank Fusion)를 사용하여 결과를 융합합니다.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from datetime import datetime

from .semantic_search import SemanticSearchEngine
from .keyword_search import KeywordSearchEngine
from .reranker import DocumentReranker
from .text_processor import TextProcessor

logger = logging.getLogger(__name__)


class HybridRetriever:
    """하이브리드 검색 시스템"""
    
    def __init__(self, 
                 chroma_manager=None,
                 embedding_client=None,
                 enable_semantic=True,
                 enable_keyword=True,
                 enable_reranking=True):
        """
        Args:
            chroma_manager: ChromaDB 매니저
            embedding_client: 임베딩 클라이언트
            enable_semantic: 의미적 검색 활성화
            enable_keyword: 키워드 검색 활성화
            enable_reranking: 재순위화 활성화
        """
        self.chroma_manager = chroma_manager
        self.embedding_client = embedding_client
        
        # 검색 엔진 초기화
        self.semantic_engine = SemanticSearchEngine(chroma_manager, embedding_client) if enable_semantic else None
        self.keyword_engine = KeywordSearchEngine() if enable_keyword else None
        self.reranker = DocumentReranker() if enable_reranking else None
        self.text_processor = TextProcessor()
        
        # 설정
        self.default_weights = {
            "semantic": 0.6,
            "keyword": 0.4
        }
        self.rrf_k = 60  # RRF 상수
        
        # 성능 통계
        self.search_stats = {
            "total_searches": 0,
            "semantic_searches": 0,
            "keyword_searches": 0,
            "hybrid_searches": 0,
            "avg_response_time": 0.0
        }
    
    async def search(self, 
                    query: str,
                    filters: Optional[Dict[str, Any]] = None,
                    top_k: int = 10,
                    search_type: str = "hybrid",
                    weights: Optional[Dict[str, float]] = None,
                    sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        하이브리드 검색 실행
        
        Args:
            query: 검색 쿼리
            filters: 검색 필터 (날짜, 소스, 화자 등)
            top_k: 반환할 결과 수
            search_type: 검색 유형 ("hybrid", "semantic", "keyword")
            weights: 검색 방식별 가중치
            sources: 검색할 소스 목록
            
        Returns:
            검색 결과
        """
        start_time = datetime.now()
        
        try:
            # 입력 검증 및 전처리
            processed_query = await self._preprocess_query(query)
            if not processed_query:
                return self._empty_result("검색 쿼리가 유효하지 않습니다.")
            
            # 검색 유형별 실행
            if search_type == "semantic" and self.semantic_engine:
                results = await self._semantic_search_only(processed_query, filters, top_k, sources)
                self.search_stats["semantic_searches"] += 1
                
            elif search_type == "keyword" and self.keyword_engine:
                results = await self._keyword_search_only(processed_query, filters, top_k, sources)
                self.search_stats["keyword_searches"] += 1
                
            else:  # hybrid
                results = await self._hybrid_search(processed_query, filters, top_k, weights or self.default_weights, sources)
                self.search_stats["hybrid_searches"] += 1
            
            # 성능 통계 업데이트
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(response_time)
            
            # 최종 결과 정리
            final_results = await self._prepare_final_results(results, query, response_time, search_type)
            
            logger.info(f"하이브리드 검색 완료: {len(results.get('documents', []))}개 결과, {response_time:.2f}초")
            return final_results
            
        except Exception as e:
            logger.error(f"하이브리드 검색 오류: {str(e)}")
            return self._empty_result(f"검색 중 오류 발생: {str(e)}")
    
    async def _preprocess_query(self, query: str) -> str:
        """쿼리 전처리"""
        
        if not query or len(query.strip()) < 2:
            return ""
        
        # 기본 정제
        processed = self.text_processor.clean_text(query.strip())
        
        # 쿼리 확장 (동의어, 관련어 추가)
        expanded = await self.text_processor.expand_query(processed)
        
        return expanded
    
    async def _semantic_search_only(self, query: str, filters: Dict, top_k: int, sources: List[str]) -> Dict[str, Any]:
        """의미적 검색만 실행"""
        
        if not self.semantic_engine:
            return {"documents": [], "scores": [], "metadata": []}
        
        return await self.semantic_engine.search(
            query=query,
            filters=filters,
            top_k=top_k,
            sources=sources
        )
    
    async def _keyword_search_only(self, query: str, filters: Dict, top_k: int, sources: List[str]) -> Dict[str, Any]:
        """키워드 검색만 실행"""
        
        if not self.keyword_engine:
            return {"documents": [], "scores": [], "metadata": []}
        
        return await self.keyword_engine.search(
            query=query,
            filters=filters,
            top_k=top_k,
            sources=sources
        )
    
    async def _hybrid_search(self, query: str, filters: Dict, top_k: int, weights: Dict[str, float], sources: List[str]) -> Dict[str, Any]:
        """하이브리드 검색 실행"""
        
        # 병렬로 의미적 검색과 키워드 검색 실행
        tasks = []
        
        if self.semantic_engine and weights.get("semantic", 0) > 0:
            semantic_task = self.semantic_engine.search(query, filters, top_k * 2, sources)  # 더 많이 검색 후 융합
            tasks.append(("semantic", semantic_task))
        
        if self.keyword_engine and weights.get("keyword", 0) > 0:
            keyword_task = self.keyword_engine.search(query, filters, top_k * 2, sources)
            tasks.append(("keyword", keyword_task))
        
        if not tasks:
            return {"documents": [], "scores": [], "metadata": []}
        
        # 병렬 실행
        search_results = {}
        for search_type, task in tasks:
            try:
                result = await task
                search_results[search_type] = result
            except Exception as e:
                logger.warning(f"{search_type} 검색 실패: {str(e)}")
                search_results[search_type] = {"documents": [], "scores": [], "metadata": []}
        
        # RRF로 결과 융합
        fused_results = await self._reciprocal_rank_fusion(search_results, weights, top_k)
        
        return fused_results
    
    async def _reciprocal_rank_fusion(self, search_results: Dict[str, Dict], weights: Dict[str, float], top_k: int) -> Dict[str, Any]:
        """RRF(Reciprocal Rank Fusion)로 검색 결과 융합"""
        
        # 문서별 점수 집계
        document_scores = {}  # doc_id -> {score, metadata, content}
        
        for search_type, results in search_results.items():
            documents = results.get("documents", [])
            scores = results.get("scores", [])
            metadata_list = results.get("metadata", [])
            
            weight = weights.get(search_type, 1.0)
            
            for rank, (doc, score, metadata) in enumerate(zip(documents, scores, metadata_list)):
                # 문서 식별자 생성 (내용 기반)
                doc_id = self._generate_doc_id(doc, metadata)
                
                # RRF 점수 계산: weight / (k + rank)
                rrf_score = weight / (self.rrf_k + rank + 1)
                
                if doc_id in document_scores:
                    # 기존 점수에 추가
                    document_scores[doc_id]["rrf_score"] += rrf_score
                    document_scores[doc_id]["original_scores"][search_type] = score
                else:
                    # 새 문서
                    document_scores[doc_id] = {
                        "content": doc,
                        "metadata": metadata,
                        "rrf_score": rrf_score,
                        "original_scores": {search_type: score},
                        "found_in": [search_type]
                    }
                
                # 검색 방식 기록
                if search_type not in document_scores[doc_id]["found_in"]:
                    document_scores[doc_id]["found_in"].append(search_type)
        
        # 점수 순으로 정렬
        sorted_docs = sorted(
            document_scores.items(),
            key=lambda x: x[1]["rrf_score"],
            reverse=True
        )
        
        # 상위 k개 선택
        top_docs = sorted_docs[:top_k]
        
        # 결과 정리
        documents = [doc_info["content"] for _, doc_info in top_docs]
        scores = [doc_info["rrf_score"] for _, doc_info in top_docs]
        metadata = [doc_info["metadata"] for _, doc_info in top_docs]
        
        # 추가 메타데이터 포함
        for i, (doc_id, doc_info) in enumerate(top_docs):
            metadata[i]["fusion_info"] = {
                "rrf_score": doc_info["rrf_score"],
                "found_in": doc_info["found_in"],
                "original_scores": doc_info["original_scores"]
            }
        
        return {
            "documents": documents,
            "scores": scores,
            "metadata": metadata,
            "fusion_stats": {
                "total_unique_docs": len(document_scores),
                "search_types_used": list(search_results.keys()),
                "weights_applied": weights
            }
        }
    
    def _generate_doc_id(self, document: str, metadata: Dict) -> str:
        """문서 고유 식별자 생성"""
        
        # 메타데이터에서 고유 식별자 추출
        if "doc_id" in metadata:
            return str(metadata["doc_id"])
        elif "source" in metadata and "title" in metadata:
            return f"{metadata['source']}_{metadata['title']}"
        else:
            # 내용의 해시 사용 (간단한 구현)
            return str(hash(document[:100]))  # 처음 100자 기반
    
    async def _prepare_final_results(self, results: Dict[str, Any], original_query: str, response_time: float, search_type: str) -> Dict[str, Any]:
        """최종 결과 정리"""
        
        documents = results.get("documents", [])
        
        # 재순위화 (옵션)
        if self.reranker and len(documents) > 1:
            try:
                reranked_results = await self.reranker.rerank(
                    query=original_query,
                    documents=documents,
                    scores=results.get("scores", []),
                    metadata=results.get("metadata", [])
                )
                results.update(reranked_results)
            except Exception as e:
                logger.warning(f"재순위화 실패: {str(e)}")
        
        # 결과에 추가 정보 포함
        final_result = {
            "query": original_query,
            "search_type": search_type,
            "results": {
                "documents": results.get("documents", []),
                "scores": results.get("scores", []),
                "metadata": results.get("metadata", [])
            },
            "search_metadata": {
                "total_results": len(results.get("documents", [])),
                "response_time_seconds": response_time,
                "search_timestamp": datetime.now().isoformat(),
                "fusion_stats": results.get("fusion_stats"),
                "reranked": bool(self.reranker and len(documents) > 1)
            },
            "suggestions": await self._generate_search_suggestions(original_query, results)
        }
        
        return final_result
    
    async def _generate_search_suggestions(self, query: str, results: Dict[str, Any]) -> List[str]:
        """검색 개선 제안 생성"""
        
        suggestions = []
        
        # 결과가 적은 경우
        if len(results.get("documents", [])) < 3:
            suggestions.append("검색어를 더 일반적인 용어로 바꿔보세요")
            suggestions.append("동의어나 관련 키워드를 추가해보세요")
        
        # 결과가 너무 많은 경우
        elif len(results.get("documents", [])) > 20:
            suggestions.append("더 구체적인 검색어를 사용해보세요")
            suggestions.append("날짜나 소스 필터를 적용해보세요")
        
        # 키워드 제안
        common_terms = self.text_processor.extract_keywords(query)
        if common_terms:
            suggestions.append(f"관련 키워드: {', '.join(common_terms[:3])}")
        
        return suggestions[:3]  # 최대 3개
    
    def _empty_result(self, message: str) -> Dict[str, Any]:
        """빈 검색 결과"""
        
        return {
            "query": "",
            "search_type": "none",
            "results": {
                "documents": [],
                "scores": [],
                "metadata": []
            },
            "search_metadata": {
                "total_results": 0,
                "response_time_seconds": 0.0,
                "search_timestamp": datetime.now().isoformat(),
                "error": message
            },
            "suggestions": ["올바른 검색어를 입력해주세요"]
        }
    
    def _update_stats(self, response_time: float):
        """검색 통계 업데이트"""
        
        self.search_stats["total_searches"] += 1
        
        # 평균 응답 시간 업데이트
        total = self.search_stats["total_searches"]
        current_avg = self.search_stats["avg_response_time"]
        self.search_stats["avg_response_time"] = (current_avg * (total - 1) + response_time) / total
    
    def get_search_stats(self) -> Dict[str, Any]:
        """검색 통계 반환"""
        
        return {
            **self.search_stats,
            "engines_enabled": {
                "semantic": self.semantic_engine is not None,
                "keyword": self.keyword_engine is not None,
                "reranker": self.reranker is not None
            },
            "configuration": {
                "default_weights": self.default_weights,
                "rrf_k": self.rrf_k
            }
        }
    
    async def update_configuration(self, config: Dict[str, Any]) -> bool:
        """검색 설정 업데이트"""
        
        try:
            if "weights" in config:
                self.default_weights.update(config["weights"])
            
            if "rrf_k" in config:
                self.rrf_k = max(1, int(config["rrf_k"]))
            
            logger.info("하이브리드 검색 설정이 업데이트되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"설정 업데이트 실패: {str(e)}")
            return False