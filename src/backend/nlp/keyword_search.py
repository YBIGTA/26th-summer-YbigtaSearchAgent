"""
키워드 검색 엔진 (KeywordSearchEngine)

전문 검색(Full Text Search) 기반 키워드 매칭을 제공합니다.
"""

import logging
import re
from typing import Dict, List, Any, Optional
import asyncio
import os
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class KeywordSearchEngine:
    """키워드 기반 검색 엔진"""
    
    def __init__(self, db_session_factory=None, index_manager=None, chroma_manager=None, llm_client=None):
        self.db_session_factory = db_session_factory
        self.index_manager = index_manager
        self.chroma_manager = chroma_manager
        self.llm_client = llm_client  # Upstage API 클라이언트
        
        # 기본 불용어 목록
        self.stopwords = set([
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
            logger.info(f"🔍 키워드 검색 시작: '{query}' (top_k={top_k})")
            
            # 쿼리 전처리
            processed_query = self._preprocess_query(query)
            if not processed_query:
                logger.warning("쿼리 전처리 후 빈 문자열")
                return {"documents": [], "scores": [], "metadata": []}
            
            # 키워드 추출
            keywords = await self._extract_keywords_with_llm(processed_query)
            logger.info(f"📝 추출된 키워드: {keywords}")
            
            # 검색 실행
            if self.db_session_factory:
                results = await self._search_in_index(keywords, filters, top_k, sources)
                logger.info(f"✅ FTS 검색 완료: {len(results.get('documents', []))}개 결과")
            else:
                logger.warning("DB 세션 팩토리가 없어 폴백 검색 사용")
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
    
    async def _extract_keywords_with_llm(self, query: str) -> List[str]:
        """LLM을 사용하여 쿼리에서 핵심 키워드 추출"""
        try:
            if not self.llm_client:
                logger.warning("LLM 클라이언트가 없어 간단한 키워드 추출 사용")
                return await self._simple_keyword_extraction(query)
            
            # LLM 프롬프트 구성
            prompt = f"""다음 질문이나 쿼리에서 검색에 필요한 핵심 키워드만 추출해주세요.
불용어, 조사, 질문어는 제외하고 실제 검색 대상이 되는 명사, 고유명사만 추출하세요.

질문/쿼리: "{query}"

핵심 키워드만 쉼표로 구분해서 답변하세요. 예시:
- "윤희찬이 누구야?" → "윤희찬"
- "김정인은 어떤 사람인가요?" → "김정인"
- "YBIGTA 회장은 누구인가요?" → "YBIGTA, 회장"
- "네트워크 강의 자료 어디에 있어?" → "네트워크, 강의, 자료"

답변:"""

            # LLM 호출
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.invoke_async(messages)
            
            # 응답 처리 (문자열 또는 딕셔너리 모두 처리)
            if response:
                if isinstance(response, str):
                    keywords_text = response.strip()
                elif isinstance(response, dict) and response.get("content"):
                    keywords_text = response["content"].strip()
                else:
                    logger.warning("LLM 응답 형식이 예상과 다름")
                    return await self._simple_keyword_extraction(query)
                
                # 응답에서 키워드 추출
                keywords = [kw.strip() for kw in keywords_text.split(",") if kw.strip()]
                
                logger.info(f"🔍 LLM 키워드 추출 결과: {keywords}")
                return keywords
            else:
                logger.warning("LLM 응답이 비어있어 간단한 키워드 추출 사용")
                return await self._simple_keyword_extraction(query)
            
        except Exception as e:
            logger.error(f"LLM 키워드 추출 실패: {e}")
            # 폴백: 간단한 키워드 추출 사용
            return await self._simple_keyword_extraction(query)
    
    async def _simple_keyword_extraction(self, query: str) -> List[str]:
        """간단한 키워드 추출 (LLM 대신 사용)"""
        # 질문 형태 처리
        question_words = ["누구", "무엇", "어떤", "어디", "언제", "왜", "어떻게", "얼마나"]
        question_endings = ["야?", "인가요?", "입니까?", "세요?", "세요", "까?"]
        
        # 질문 형태인지 확인
        is_question = any(word in query for word in question_words) or any(query.endswith(ending) for ending in question_endings)
        
        if is_question:
            # 질문에서 핵심 키워드만 추출
            # "윤희찬이 누구야?" -> "윤희찬"
            # "김정인은 어떤 사람인가요?" -> "김정인"
            words = query.split()
            keywords = []
            
            for word in words:
                # 질문 단어나 조사 제거
                if word in question_words or word in ["이", "은", "는", "가", "을", "를", "의", "에", "에서", "로", "으로", "와", "과", "하고", "며", "면서"]:
                    continue
                # 질문 어미 제거
                if any(word.endswith(ending.replace("?", "")) for ending in question_endings):
                    continue
                # 불용어 제거
                if word.lower() in self.stopwords:
                    continue
                # 빈 문자열이나 너무 짧은 단어 제거
                if len(word.strip()) < 2:
                    continue
                    
                keywords.append(word.strip())
            
            logger.info(f"🔍 간단한 키워드 추출 결과: {keywords}")
            return keywords
        else:
            # 일반 쿼리의 경우 기존 로직 사용
            words = query.split()
            keywords = []
            
            for word in words:
                if word.lower() in self.stopwords:
                    continue
                if len(word.strip()) < 2:
                    continue
                keywords.append(word.strip())
            
            logger.info(f"🔍 일반 키워드 추출 결과: {keywords}")
            return keywords
    
    def _extract_keywords_fallback(self, query: str) -> List[str]:
        """폴백 키워드 추출 로직"""
        return self._extract_keywords(query)
    
    def _extract_keywords(self, query: str) -> List[str]:
        """기존 키워드 추출 로직 (하위 호환성)"""
        
        # 기본 정제
        query = re.sub(r'[^\w\s가-힣]', ' ', query)  # 특수문자 제거
        query = re.sub(r'\s+', ' ', query).strip()   # 공백 정리
        
        return query.lower().split()
    
    async def _search_in_index(self, 
                              keywords: List[str], 
                              filters: Optional[Dict], 
                              top_k: int, 
                              sources: Optional[List[str]]) -> Dict[str, Any]:
        """ChromaDB 기반 키워드 검색"""
        
        try:
            # ChromaDB 매니저가 있는지 확인
            if hasattr(self, 'chroma_manager') and self.chroma_manager:
                return await self._search_in_chroma(keywords, filters, top_k, sources)
            else:
                logger.warning("ChromaDB 매니저가 설정되지 않았습니다.")
                return await self._fallback_search(keywords, " ".join(keywords), top_k)
            
        except Exception as e:
            logger.error(f"키워드 검색 오류: {str(e)}")
            return {"documents": [], "scores": [], "metadata": []}
    
    async def _search_in_chroma(self, keywords: List[str], filters: Optional[Dict], top_k: int, sources: Optional[List[str]]) -> Dict[str, Any]:
        """ChromaDB에서 키워드 검색"""
        
        try:
            # ChromaDB 매니저가 있는지 확인
            if not self.chroma_manager:
                logger.warning("ChromaDB 매니저가 설정되지 않았습니다.")
                return {"documents": [], "scores": [], "metadata": []}
            
            # ChromaDB 컬렉션에서 직접 검색
            all_documents = []
            
            # Unified DB에서 검색
            if hasattr(self.chroma_manager, 'unified_adapter') and self.chroma_manager.unified_adapter.available:
                try:
                    # 모든 문서를 가져와서 키워드 매칭
                    collection = self.chroma_manager.unified_adapter.collection
                    if collection:
                        # ChromaDB에서 모든 문서 가져오기
                        results = collection.get(include=['documents', 'metadatas'])
                        
                        if results and results['documents']:
                            for i, doc_content in enumerate(results['documents']):
                                doc_metadata = results['metadatas'][i] if results['metadatas'] else {}
                                
                                # 키워드 매칭 점수 계산
                                score = 0
                                for keyword in keywords:
                                    if keyword.lower() in doc_content.lower():
                                        score += doc_content.lower().count(keyword.lower())
                                    if keyword.lower() in doc_metadata.get('title', '').lower():
                                        score += doc_metadata.get('title', '').lower().count(keyword.lower()) * 2
                                
                                if score > 0:
                                    all_documents.append({
                                        'content': doc_content,
                                        'metadata': doc_metadata,
                                        'score': score
                                    })
                        
                        logger.info(f"🔍 Unified DB에서 {len(all_documents)}개 문서 매칭")
                except Exception as e:
                    logger.error(f"Unified DB 검색 오류: {e}")
            
            # Incremental DB에서 검색
            if hasattr(self.chroma_manager, 'incremental_manager') and self.chroma_manager.incremental_manager.available:
                try:
                    collection = self.chroma_manager.incremental_manager.collection
                    if collection:
                        results = collection.get(include=['documents', 'metadatas'])
                        
                        if results and results['documents']:
                            for i, doc_content in enumerate(results['documents']):
                                doc_metadata = results['metadatas'][i] if results['metadatas'] else {}
                                
                                # 키워드 매칭 점수 계산
                                score = 0
                                for keyword in keywords:
                                    if keyword.lower() in doc_content.lower():
                                        score += doc_content.lower().count(keyword.lower())
                                    if keyword.lower() in doc_metadata.get('title', '').lower():
                                        score += doc_metadata.get('title', '').lower().count(keyword.lower()) * 2
                                
                                if score > 0:
                                    all_documents.append({
                                        'content': doc_content,
                                        'metadata': doc_metadata,
                                        'score': score
                                    })
                        
                        logger.info(f"🔍 Incremental DB에서 {len([d for d in all_documents if d['metadata'].get('storage') == 'incremental'])}개 문서 매칭")
                except Exception as e:
                    logger.error(f"Incremental DB 검색 오류: {e}")
            
            # 점수 순으로 정렬하고 상위 결과 반환
            all_documents.sort(key=lambda x: x['score'], reverse=True)
            
            documents = [doc['content'] for doc in all_documents[:top_k]]
            scores = [doc['score'] for doc in all_documents[:top_k]]
            metadata = [doc['metadata'] for doc in all_documents[:top_k]]
            
            logger.info(f"🔍 키워드 검색 결과: {len(documents)}개 문서 (키워드: {keywords})")
            
            return {
                "documents": documents,
                "scores": scores,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"ChromaDB 키워드 검색 오류: {str(e)}")
            return {"documents": [], "scores": [], "metadata": []}
    
    def _build_fts_query(self, keywords: List[str]) -> str:
        """FTS 쿼리 구성"""
        if not keywords:
            return ""
        
        # 각 키워드를 큰따옴표로 감싸고 OR로 연결
        quoted_keywords = [f'"{keyword}"' for keyword in keywords]
        return " OR ".join(quoted_keywords)
    
    def _build_where_conditions(self, filters: Optional[Dict], sources: Optional[List[str]]) -> str:
        """WHERE 조건 구성"""
        conditions = []
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, str):
                    conditions.append(f"d.{key} = '{value}'")
                elif isinstance(value, list):
                    placeholders = "', '".join(value)
                    conditions.append(f"d.{key} IN ('{placeholders}')")
                else:
                    conditions.append(f"d.{key} = {value}")
        
        if sources:
            placeholders = "', '".join(sources)
            conditions.append(f"d.source IN ('{placeholders}')")
        
        return " AND ".join(conditions) if conditions else "1=1"
    
    async def _execute_fts_query(self, session: Session, fts_query: str, where_conditions: str, top_k: int) -> Dict[str, Any]:
        """FTS 쿼리 실행"""
        
        logger.info(f"🔍 FTS 쿼리 실행: '{fts_query}' (top_k={top_k})")
        
        # FTS 검색과 documents 테이블 JOIN
        sql_query = f"""
        SELECT 
            d.id,
            d.title,
            d.content,
            d.source,
            d.url,
            d.doc_metadata,
            fts.rank,
            fts.highlight(document_fts, 0, '<mark>', '</mark>') as highlighted_content
        FROM document_fts fts
        JOIN documents d ON fts.rowid = d.id
        WHERE document_fts MATCH :query AND {where_conditions}
        ORDER BY fts.rank
        LIMIT :limit
        """
        
        try:
            logger.info(f"📝 SQL 쿼리: {sql_query}")
            logger.info(f"📝 파라미터: query='{fts_query}', limit={top_k}")
            
            # SQLAlchemy의 명명된 파라미터 사용
            result = session.execute(text(sql_query), {"query": fts_query, "limit": top_k})
            rows = result.fetchall()
            
            logger.info(f"📊 FTS 쿼리 결과: {len(rows)}개 행")
            
            documents = []
            scores = []
            metadata = []
            
            for i, row in enumerate(rows):
                # FTS rank를 점수로 변환 (rank가 낮을수록 높은 점수)
                # rank는 0에 가까울수록 더 관련성이 높음
                score = self._convert_rank_to_score(row.rank)
                
                documents.append(row.content or "")
                scores.append(score)
                metadata.append({
                    "id": row.id,
                    "title": row.title,
                    "source": row.source,
                    "url": row.url,
                    "highlighted_content": row.highlighted_content,
                    "doc_metadata": row.doc_metadata,
                    "rank": row.rank,
                    "type": "fts_search"
                })
                
                if i < 3:  # 처음 3개 결과만 로그
                    logger.info(f"  📄 결과 {i+1}: {row.title} (rank={row.rank}, score={score:.3f})")
            
            logger.info(f"✅ FTS 검색 완료: {len(documents)}개 문서")
            
            return {
                "documents": documents,
                "scores": scores,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"FTS 쿼리 실행 오류: {str(e)}")
            return {"documents": [], "scores": [], "metadata": []}
    
    def _convert_rank_to_score(self, rank: float) -> float:
        """FTS rank를 점수로 변환"""
        # FTS rank는 0에 가까울수록 더 관련성이 높음
        # 0~1 범위의 점수로 변환
        if rank == 0:
            return 1.0
        elif rank < 0:
            return 0.5  # 음수 rank는 중간 점수
        else:
            # rank가 클수록 점수 감소 (최소 0.1)
            return max(0.1, 1.0 / (1.0 + rank))
    
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
            "engine_type": "keyword_fts",
            "stopwords_count": len(self.stopwords),
            "database_available": self.db_session_factory is not None,
            "index_available": self.index_manager is not None,
            "supported_features": [
                "fts5_search",
                "exact_match",
                "keyword_highlighting",
                "rank_scoring",
                "metadata_filtering"
            ]
        }