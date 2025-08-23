"""
문서 재순위화 시스템 (DocumentReranker)

LLM 기반 문맥적 재순위화를 통해 검색 결과의 품질을 향상시킵니다.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import asyncio

logger = logging.getLogger(__name__)


class DocumentReranker:
    """LLM 기반 문서 재순위화 시스템"""
    
    def __init__(self, llm_client=None, max_rerank_count=20):
        self.llm_client = llm_client
        self.max_rerank_count = max_rerank_count
        
        # 재순위화 전략
        self.strategies = {
            "contextual": self._contextual_reranking,
            "semantic_similarity": self._semantic_similarity_reranking,
            "query_intent": self._query_intent_reranking,
            "hybrid": self._hybrid_reranking
        }
        
        # 성능 통계
        self.reranking_stats = {
            "total_rerankings": 0,
            "avg_improvement": 0.0,
            "strategy_usage": {strategy: 0 for strategy in self.strategies.keys()}
        }
    
    async def rerank(self, 
                    query: str,
                    documents: List[str],
                    scores: List[float],
                    metadata: List[Dict[str, Any]],
                    strategy: str = "hybrid",
                    top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        문서 재순위화 실행
        
        Args:
            query: 원본 검색 쿼리
            documents: 검색된 문서들
            scores: 원본 검색 점수들
            metadata: 문서 메타데이터들
            strategy: 재순위화 전략
            top_k: 최종 반환할 문서 수
            
        Returns:
            재순위화된 결과
        """
        try:
            if not documents or len(documents) <= 1:
                return {
                    "documents": documents,
                    "scores": scores,
                    "metadata": metadata
                }
            
            # 재순위화할 문서 수 제한
            rerank_count = min(len(documents), self.max_rerank_count)
            documents_to_rerank = documents[:rerank_count]
            scores_to_rerank = scores[:rerank_count]
            metadata_to_rerank = metadata[:rerank_count]
            
            # 선택된 전략으로 재순위화
            if strategy in self.strategies:
                reranked_results = await self.strategies[strategy](
                    query, documents_to_rerank, scores_to_rerank, metadata_to_rerank
                )
                self.reranking_stats["strategy_usage"][strategy] += 1
            else:
                logger.warning(f"알 수 없는 재순위화 전략: {strategy}")
                reranked_results = await self._hybrid_reranking(
                    query, documents_to_rerank, scores_to_rerank, metadata_to_rerank
                )
            
            # 나머지 문서들 추가 (재순위화하지 않은 것들)
            if len(documents) > rerank_count:
                reranked_results["documents"].extend(documents[rerank_count:])
                reranked_results["scores"].extend(scores[rerank_count:])
                reranked_results["metadata"].extend(metadata[rerank_count:])
            
            # top_k 적용
            if top_k and top_k < len(reranked_results["documents"]):
                reranked_results = {
                    "documents": reranked_results["documents"][:top_k],
                    "scores": reranked_results["scores"][:top_k],
                    "metadata": reranked_results["metadata"][:top_k]
                }
            
            # 통계 업데이트
            self.reranking_stats["total_rerankings"] += 1
            
            # 재순위화 정보 추가
            for i, meta in enumerate(reranked_results["metadata"]):
                meta["reranking_info"] = {
                    "strategy_used": strategy,
                    "original_rank": documents.index(reranked_results["documents"][i]) if reranked_results["documents"][i] in documents else -1,
                    "new_rank": i,
                    "reranked": True
                }
            
            logger.info(f"문서 재순위화 완료: {len(documents_to_rerank)}개 문서, 전략: {strategy}")
            return reranked_results
            
        except Exception as e:
            logger.error(f"문서 재순위화 오류: {str(e)}")
            return {
                "documents": documents,
                "scores": scores,
                "metadata": metadata
            }
    
    async def _contextual_reranking(self, query: str, documents: List[str], scores: List[float], metadata: List[Dict]) -> Dict[str, Any]:
        """문맥적 재순위화 (LLM 기반)"""
        
        if not self.llm_client:
            logger.warning("LLM 클라이언트가 설정되지 않아 문맥적 재순위화를 수행할 수 없습니다.")
            return {
                "documents": documents,
                "scores": scores,
                "metadata": metadata
            }
        
        try:
            # 각 문서의 관련성을 LLM으로 평가
            relevance_scores = []
            
            for doc in documents:
                relevance_score = await self._evaluate_document_relevance(query, doc)
                relevance_scores.append(relevance_score)
            
            # 관련성 점수로 재정렬
            sorted_indices = sorted(
                range(len(documents)), 
                key=lambda i: relevance_scores[i], 
                reverse=True
            )
            
            return {
                "documents": [documents[i] for i in sorted_indices],
                "scores": [relevance_scores[i] for i in sorted_indices],
                "metadata": [metadata[i] for i in sorted_indices]
            }
            
        except Exception as e:
            logger.error(f"문맥적 재순위화 오류: {str(e)}")
            return {"documents": documents, "scores": scores, "metadata": metadata}
    
    async def _evaluate_document_relevance(self, query: str, document: str) -> float:
        """LLM을 사용한 문서 관련성 평가"""
        
        # 문서가 너무 긴 경우 요약
        doc_excerpt = document[:500] + "..." if len(document) > 500 else document
        
        prompt = f"""
다음 쿼리에 대해 이 문서가 얼마나 관련이 있는지 0.0부터 1.0까지의 점수로 평가하세요.

쿼리: {query}

문서 내용:
{doc_excerpt}

평가 기준:
1. 내용의 직접적 관련성
2. 정보의 정확성과 신뢰성
3. 사용자 의도와의 일치도
4. 정보의 완성도

점수만 숫자로 답하세요 (예: 0.85):
"""
        
        try:
            # TODO: 실제 LLM API 호출
            # response = await self.llm_client.generate(prompt)
            # score = float(response.strip())
            
            # 임시 더미 점수 (실제로는 LLM 응답 파싱)
            import random
            score = random.uniform(0.3, 0.95)
            
            return max(0.0, min(1.0, score))  # 0-1 범위 보장
            
        except Exception as e:
            logger.error(f"문서 관련성 평가 오류: {str(e)}")
            return 0.5  # 기본값
    
    async def _semantic_similarity_reranking(self, query: str, documents: List[str], scores: List[float], metadata: List[Dict]) -> Dict[str, Any]:
        """의미적 유사도 기반 재순위화"""
        
        # 간단한 키워드 매칭 기반 유사도 계산
        query_words = set(query.lower().split())
        
        similarity_scores = []
        for doc in documents:
            doc_words = set(doc.lower().split())
            
            # Jaccard 유사도 계산
            intersection = len(query_words & doc_words)
            union = len(query_words | doc_words)
            jaccard_similarity = intersection / union if union > 0 else 0.0
            
            # 원본 점수와 결합
            combined_score = (jaccard_similarity * 0.7) + (scores[documents.index(doc)] * 0.3)
            similarity_scores.append(combined_score)
        
        # 점수순으로 정렬
        sorted_indices = sorted(
            range(len(documents)), 
            key=lambda i: similarity_scores[i], 
            reverse=True
        )
        
        return {
            "documents": [documents[i] for i in sorted_indices],
            "scores": [similarity_scores[i] for i in sorted_indices],
            "metadata": [metadata[i] for i in sorted_indices]
        }
    
    async def _query_intent_reranking(self, query: str, documents: List[str], scores: List[float], metadata: List[Dict]) -> Dict[str, Any]:
        """쿼리 의도 기반 재순위화"""
        
        # 쿼리 의도 분류
        intent = self._classify_query_intent(query)
        
        # 의도별 가중치 적용
        intent_weights = {
            "factual": {"type": "document", "weight": 1.2},
            "analytical": {"type": "analysis", "weight": 1.3},
            "procedural": {"type": "guide", "weight": 1.1},
            "conversational": {"type": "discussion", "weight": 1.0}
        }
        
        adjusted_scores = []
        for i, (doc, score, meta) in enumerate(zip(documents, scores, metadata)):
            base_score = score
            
            # 메타데이터 기반 가중치 적용
            doc_type = meta.get("type", "unknown")
            if intent in intent_weights:
                target_type = intent_weights[intent]["type"]
                weight = intent_weights[intent]["weight"]
                
                if doc_type == target_type:
                    adjusted_score = base_score * weight
                else:
                    adjusted_score = base_score * 0.9  # 약간 감점
            else:
                adjusted_score = base_score
            
            adjusted_scores.append(adjusted_score)
        
        # 조정된 점수로 정렬
        sorted_indices = sorted(
            range(len(documents)), 
            key=lambda i: adjusted_scores[i], 
            reverse=True
        )
        
        return {
            "documents": [documents[i] for i in sorted_indices],
            "scores": [adjusted_scores[i] for i in sorted_indices],
            "metadata": [metadata[i] for i in sorted_indices]
        }
    
    def _classify_query_intent(self, query: str) -> str:
        """쿼리 의도 분류 (간단한 규칙 기반)"""
        
        query_lower = query.lower()
        
        # 사실적 질문 패턴
        factual_patterns = ["무엇", "누구", "언제", "어디", "얼마", "what", "who", "when", "where", "how much"]
        if any(pattern in query_lower for pattern in factual_patterns):
            return "factual"
        
        # 분석적 질문 패턴
        analytical_patterns = ["왜", "어떻게", "분석", "비교", "평가", "why", "how", "analyze", "compare", "evaluate"]
        if any(pattern in query_lower for pattern in analytical_patterns):
            return "analytical"
        
        # 절차적 질문 패턴
        procedural_patterns = ["방법", "절차", "단계", "설치", "설정", "how to", "step", "install", "setup"]
        if any(pattern in query_lower for pattern in procedural_patterns):
            return "procedural"
        
        return "conversational"  # 기본값
    
    async def _hybrid_reranking(self, query: str, documents: List[str], scores: List[float], metadata: List[Dict]) -> Dict[str, Any]:
        """하이브리드 재순위화 (여러 전략 결합)"""
        
        # 각 전략별 결과 계산
        strategies_results = {}
        
        try:
            # 의미적 유사도 재순위화
            sem_result = await self._semantic_similarity_reranking(query, documents, scores, metadata)
            strategies_results["semantic"] = sem_result
        except:
            strategies_results["semantic"] = {"documents": documents, "scores": scores, "metadata": metadata}
        
        try:
            # 쿼리 의도 재순위화
            intent_result = await self._query_intent_reranking(query, documents, scores, metadata)
            strategies_results["intent"] = intent_result
        except:
            strategies_results["intent"] = {"documents": documents, "scores": scores, "metadata": metadata}
        
        # 전략별 가중치
        strategy_weights = {
            "semantic": 0.4,
            "intent": 0.3,
            "original": 0.3
        }
        
        # 문서별 최종 점수 계산
        final_scores = {}
        
        for doc in documents:
            doc_scores = []
            
            # 각 전략에서의 점수 수집
            for strategy_name, result in strategies_results.items():
                try:
                    doc_index = result["documents"].index(doc)
                    score = result["scores"][doc_index]
                    weight = strategy_weights.get(strategy_name, 0.0)
                    doc_scores.append(score * weight)
                except (ValueError, IndexError):
                    continue
            
            # 원본 점수도 포함
            original_score = scores[documents.index(doc)]
            doc_scores.append(original_score * strategy_weights["original"])
            
            # 최종 점수
            final_scores[doc] = sum(doc_scores) if doc_scores else original_score
        
        # 최종 점수로 정렬
        sorted_docs = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 결과 정리
        reranked_documents = [doc for doc, score in sorted_docs]
        reranked_scores = [score for doc, score in sorted_docs]
        reranked_metadata = [metadata[documents.index(doc)] for doc, score in sorted_docs]
        
        return {
            "documents": reranked_documents,
            "scores": reranked_scores,
            "metadata": reranked_metadata
        }
    
    def get_reranking_stats(self) -> Dict[str, Any]:
        """재순위화 통계 반환"""
        
        return {
            **self.reranking_stats,
            "available_strategies": list(self.strategies.keys()),
            "max_rerank_count": self.max_rerank_count,
            "llm_enabled": self.llm_client is not None
        }
    
    def update_configuration(self, config: Dict[str, Any]) -> bool:
        """재순위화 설정 업데이트"""
        
        try:
            if "max_rerank_count" in config:
                self.max_rerank_count = max(1, int(config["max_rerank_count"]))
            
            logger.info("재순위화 설정이 업데이트되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"설정 업데이트 실패: {str(e)}")
            return False