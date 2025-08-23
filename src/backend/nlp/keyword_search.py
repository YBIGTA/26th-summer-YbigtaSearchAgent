"""
키워드 검색 엔진 (KeywordSearchEngine)

전문 검색(Full Text Search) 기반 키워드 매칭을 제공합니다.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class KeywordSearchEngine:
    """키워드 기반 검색 엔진"""
    
    def __init__(self, index_manager=None):
        self.index_manager = index_manager
        self.stopwords = set([
            "은", "는", "이", "가", "을", "를", "에", "의", "와", "과", 
            "도", "만", "에서", "로", "으로", "부터", "까지", "에게",
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"
        ])
    
    async def search(self, 
                    query: str, 
                    filters: Optional[Dict[str, Any]] = None, 
                    top_k: int = 10, 
                    sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        키워드 검색 실행
        
        Args:
            query: 검색 쿼리
            filters: 검색 필터
            top_k: 반환할 결과 수
            sources: 검색할 소스 목록
            
        Returns:
            검색 결과
        """
        try:
            # 쿼리 전처리
            processed_query = self._preprocess_query(query)
            if not processed_query:
                return {"documents": [], "scores": [], "metadata": []}
            
            # 키워드 추출
            keywords = self._extract_keywords(processed_query)
            
            # 검색 실행
            if self.index_manager:
                results = await self._search_in_index(keywords, filters, top_k, sources)
            else:
                results = await self._fallback_search(keywords, query, top_k)
            
            return results
            
        except Exception as e:
            logger.error(f"키워드 검색 오류: {str(e)}")
            return {"documents": [], "scores": [], "metadata": []}
    
    def _preprocess_query(self, query: str) -> str:
        """쿼리 전처리"""
        
        # 기본 정제
        query = re.sub(r'[^\w\s가-힣]', ' ', query)  # 특수문자 제거
        query = re.sub(r'\s+', ' ', query).strip()   # 공백 정리
        
        return query.lower()
    
    def _extract_keywords(self, query: str) -> List[str]:
        """키워드 추출"""
        
        words = query.split()
        
        # 불용어 제거
        keywords = [word for word in words if word not in self.stopwords and len(word) > 1]
        
        # 중요도 순 정렬 (길이 기반 간단 구현)
        keywords.sort(key=len, reverse=True)
        
        return keywords[:10]  # 최대 10개 키워드
    
    async def _search_in_index(self, 
                              keywords: List[str], 
                              filters: Optional[Dict], 
                              top_k: int, 
                              sources: Optional[List[str]]) -> Dict[str, Any]:
        """인덱스에서 검색 (실제 구현)"""
        
        try:
            # TODO: 실제 전문 검색 인덱스 연동 (예: PostgreSQL FTS, Elasticsearch)
            # 현재는 더미 구현
            
            documents = []
            scores = []
            metadata = []
            
            for i, keyword in enumerate(keywords[:top_k]):
                documents.append(f"키워드 검색 결과: '{keyword}' 관련 문서")
                scores.append(1.0 - (i * 0.1))  # 순서대로 점수 감소
                metadata.append({
                    "source": "keyword",
                    "type": "document",
                    "matched_keywords": [keyword],
                    "match_type": "exact"
                })
            
            return {
                "documents": documents,
                "scores": scores,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"인덱스 검색 오류: {str(e)}")
            return {"documents": [], "scores": [], "metadata": []}
    
    async def _fallback_search(self, keywords: List[str], original_query: str, top_k: int) -> Dict[str, Any]:
        """폴백 검색 (인덱스가 없을 때)"""
        
        # 단순한 키워드 매칭 시뮬레이션
        documents = []
        scores = []
        metadata = []
        
        for i, keyword in enumerate(keywords[:top_k]):
            documents.append(f"폴백 검색 결과: '{keyword}' 포함 문서 ('{original_query}' 검색)")
            scores.append(max(0.5 - (i * 0.05), 0.1))  # 의미적 검색보다 낮은 점수
            metadata.append({
                "source": "fallback",
                "type": "keyword_match",
                "matched_keywords": [keyword],
                "match_type": "contains"
            })
        
        return {
            "documents": documents,
            "scores": scores,
            "metadata": metadata
        }
    
    def calculate_tf_idf_score(self, term: str, document: str, corpus: List[str]) -> float:
        """TF-IDF 점수 계산 (간단 구현)"""
        
        # 용어 빈도 (TF)
        doc_words = document.lower().split()
        tf = doc_words.count(term.lower()) / len(doc_words) if doc_words else 0
        
        # 문서 빈도 (DF)
        df = sum(1 for doc in corpus if term.lower() in doc.lower().split())
        
        # 역문서 빈도 (IDF)
        import math
        idf = math.log(len(corpus) / (df + 1)) if df > 0 else 0
        
        return tf * idf
    
    def fuzzy_match_score(self, query_word: str, document_word: str) -> float:
        """퍼지 매칭 점수 (레벤슈타인 거리 기반)"""
        
        def levenshtein_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        distance = levenshtein_distance(query_word.lower(), document_word.lower())
        max_len = max(len(query_word), len(document_word))
        
        if max_len == 0:
            return 1.0
        
        return 1.0 - (distance / max_len)
    
    def get_search_stats(self) -> Dict[str, Any]:
        """검색 통계 반환"""
        
        return {
            "engine_type": "keyword",
            "stopwords_count": len(self.stopwords),
            "index_available": self.index_manager is not None,
            "supported_features": [
                "exact_match",
                "fuzzy_match", 
                "tf_idf_scoring",
                "keyword_highlighting"
            ]
        }