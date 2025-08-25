"""
SimpleMeetingAnalyzer - 단순한 2단계 회의 분석기

복잡한 멀티에이전트 시스템을 대체하는 간단하고 효율적인 분석기
1단계: 전사 내용 요약 (LLM 요청)
2단계: 요약 + RAG 자료 → 분석/조언/인사이트 도출 (LLM 요청)
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SimpleMeetingAnalyzer:
    """단순한 2단계 회의 분석기"""
    
    def __init__(self, llm_client=None, chroma_manager=None, embedding_client=None):
        self.llm_client = llm_client
        self.chroma_manager = chroma_manager
        self.embedding_client = embedding_client
        logger.info("SimpleMeetingAnalyzer 초기화 완료")
    
    async def analyze_meeting(self, transcript_text: str, segments: List[Dict] = None) -> Dict[str, Any]:
        """
        메인 분석 함수 - 2단계 프로세스
        1단계: 전사 내용 요약
        2단계: 요약 + RAG 자료로 분석/조언/인사이트 생성
        """
        logger.info("회의 분석 시작 - 2단계 프로세스")
        
        try:
            # 1단계: 전사 내용 요약
            logger.info("1단계: 전사 내용 요약 중...")
            summary = await self._summarize_transcript(transcript_text)
            logger.info(f"전사 요약 완료 - 원본: {len(transcript_text)}자 → 요약: {len(summary)}자")
            
            # 2단계: 요약 + RAG 자료로 분석/조언/인사이트 생성
            logger.info("2단계: 관련 자료 검색 및 분석/인사이트 생성 중...")
            analysis_result = await self._generate_analysis_with_context(summary, transcript_text)
            
            # 기본 메타데이터 추가
            analysis_result.update({
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "transcript_length": len(transcript_text),
                "summary_length": len(summary),
                "segments_count": len(segments) if segments else 0,
                "processing_method": "simple_2step_analysis"
            })
            
            logger.info("회의 분석 완료")
            return analysis_result
            
        except Exception as e:
            logger.error(f"회의 분석 중 오류: {e}")
            return {
                "error": str(e),
                "overview": "회의 분석 중 오류가 발생했습니다",
                "key_points": [],
                "main_topics": [],
                "decisions": [],
                "action_items": [],
                "insights": [],
                "recommendations": [],
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
    
    async def _summarize_transcript(self, transcript_text: str) -> str:
        """1단계: 전사 내용을 LLM으로 요약"""
        if not self.llm_client:
            logger.warning("LLM 클라이언트가 없어 전체 원본을 반환합니다")
            return transcript_text
        
        prompt = f"""다음 회의 내용을 핵심 내용 중심으로 보고서를 작성하고, 내용에 대한 발언자들의 주장, 입장 및 논점 등에 대해 상세하게 논하세요. 

중요한 논의사항, 결정사항, 액션아이템이 있다면 포함시켜주세요.

=== 회의 전사 내용 ===
{transcript_text}
======================

요약:"""
        
        try:
            response = await self.llm_client.invoke_async(
                messages=[{"role": "user", "content": prompt}]
            )
            
            summary = response.strip() if response else "요약을 생성할 수 없습니다"
            return summary
            
        except Exception as e:
            logger.error(f"전사 요약 중 오류: {e}")
            # 오류 시 전체 원본 텍스트 반환
            return transcript_text
    
    def _search_related_documents(self, summary: str) -> str:
        """ChromaDB에서 요약과 관련된 문서 검색"""
        if not self.chroma_manager:
            logger.warning("ChromaDB 매니저가 없어 참고 자료 검색을 건너뜁니다")
            return "참고 자료를 검색할 수 없습니다."
        
        try:
            # 요약에서 키워드 추출하여 검색
            search_queries = self._extract_keywords_from_summary(summary)
            
            all_results = []
            seen_contents = set()  # 중복 결과 방지
            
            for query in search_queries[:3]:  # 상위 3개 키워드로 검색
                try:
                    # ChromaDB 검색 메서드 확인 및 호출 (동기 호출)
                    if hasattr(self.chroma_manager, 'vector_search'):
                        # 임베딩 생성 후 vector_search 호출
                        if self.embedding_client:
                            try:
                                query_embedding = self.embedding_client.embed_query(query)
                                results = self.chroma_manager.vector_search(
                                    query=query,
                                    query_embedding=query_embedding,
                                    top_k=3  # 각 키워드당 3개씩 (더 많은 후보)
                                )
                                
                                # 결과 필터링 및 스코어링
                                if results:
                                    for result in results:
                                        content = result.get('content', result.get('text', ''))
                                        # 중복 체크 (내용의 처음 100자 기준)
                                        content_key = content[:100]
                                        if content_key not in seen_contents and len(content) > 50:
                                            seen_contents.add(content_key)
                                            # 검색어와의 관련성 점수 추가
                                            result['search_query'] = query
                                            all_results.append(result)
                                            
                            except Exception as embed_error:
                                logger.warning(f"임베딩 생성 실패: {embed_error}, 다른 검색 방법 시도")
                                continue
                        else:
                            logger.warning(f"임베딩 클라이언트가 없어 '{query}' 검색을 건너뜁니다")
                            continue
                    elif hasattr(self.chroma_manager, 'search_documents'):
                        # search_documents도 임베딩이 필요한 경우 처리
                        if self.embedding_client:
                            try:
                                query_embedding = self.embedding_client.embed_query(query)
                                results = self.chroma_manager.search_documents(
                                    query=query,
                                    query_embedding=query_embedding,
                                    top_k=2
                                )
                            except Exception as embed_error:
                                logger.warning(f"search_documents 임베딩 실패: {embed_error}")
                                continue
                        else:
                            # 임베딩 없이 시도
                            try:
                                results = self.chroma_manager.search_documents(
                                    query=query, 
                                    top_k=2
                                )
                            except Exception as search_error:
                                logger.warning(f"search_documents 실패: {search_error}")
                                continue
                    elif hasattr(self.chroma_manager, 'search'):
                        try:
                            results = self.chroma_manager.search(
                                query=query, 
                                n_results=2
                            )
                        except Exception as search_error:
                            logger.warning(f"기본 search 실패: {search_error}")
                            continue
                    else:
                        logger.warning("ChromaDB 검색 메서드를 찾을 수 없습니다")
                        continue
                        
                    if results:
                        all_results.extend(results)
                except Exception as e:
                    logger.warning(f"'{query}' 검색 중 오류: {e}")
                    continue
            
            if not all_results:
                return "관련 참고 자료를 찾지 못했습니다."
            
            # 검색 결과를 텍스트로 포맷팅 (개선된 버전)
            formatted_results = []
            for i, result in enumerate(all_results[:5], 1):  # 최대 5개
                content = result.get('content', result.get('text', '내용 없음'))
                metadata = result.get('metadata', {})
                source = result.get('source', metadata.get('source', '출처 불명'))
                
                # 소스 타입별 포맷팅
                if 'github' in source:
                    source_type = "GitHub"
                elif 'notion' in source:
                    source_type = "Notion"
                elif '.pdf' in source:
                    source_type = "PDF"
                else:
                    source_type = "문서"
                
                # 내용 요약 (너무 길면 자르기)
                if len(content) > 200:
                    content = content[:200] + "..."
                
                # 더 읽기 쉬운 형태로 포맷팅
                formatted_results.append(f"**참고자료 {i}** [{source_type}]\n{content}\n")
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"관련 문서 검색 중 오류: {e}")
            return "참고 자료 검색 중 오류가 발생했습니다."
    
    async def _extract_keywords_from_summary(self, summary: str) -> List[str]:
        """LLM을 사용한 고품질 키워드 추출"""
        if not self.llm_client:
            logger.warning("LLM 클라이언트가 없어 기본 키워드 추출 방식 사용")
            return self._fallback_keyword_extraction(summary)
        
        try:
            prompt = f"""다음 회의 요약에서 관련 자료를 검색하기 위한 핵심 키워드 3-5개를 추출해주세요.

회의 요약:
{summary}

다음 조건을 만족하는 키워드를 추출해주세요:
1. 검색에 유용한 구체적인 명사나 핵심 개념
2. 너무 일반적이지 않은 특별한 용어 우선  
3. 기술적 용어, 프로젝트명, 도구명, 서비스명 포함
4. 각 키워드는 1-3단어로 구성

키워드만 쉼표로 구분하여 답변해주세요.
예: 케이터링, 홈커밍데이, 업스테이지, 해커톤"""

            response = await self.llm_client.invoke_async([{"role": "user", "content": prompt}])
            
            if response:
                # 응답에서 키워드 추출
                keywords = [k.strip() for k in response.split(',')]
                keywords = [k for k in keywords if len(k) > 1 and len(k) < 20][:5]
                
                if keywords:
                    logger.info(f"LLM 키워드 추출 성공: {keywords}")
                    return keywords
        
        except Exception as e:
            logger.warning(f"LLM 키워드 추출 실패: {e}")
        
        # 폴백: 기본 방식
        return self._fallback_keyword_extraction(summary)
    
    def _fallback_keyword_extraction(self, summary: str) -> List[str]:
        """LLM 실패 시 사용할 기본 키워드 추출"""
        import re
        
        # 주요 키워드 패턴 매칭
        important_patterns = [
            r'케이터링', r'홈커밍', r'행사', r'파티', r'회의', 
            r'프로젝트', r'업스테이지', r'해커톤', r'교육', r'세션'
        ]
        
        keywords = []
        for pattern in important_patterns:
            if re.search(pattern, summary, re.IGNORECASE):
                keywords.append(pattern)
        
        # 3글자 이상 명사 추가
        words = re.findall(r'[가-힣]{3,}', summary)
        stopwords = {'그래서', '하지만', '그런데', '따라서', '또한', '같은', '대해', '통해', '위해', '경우', '때문'}
        words = [w for w in words if w not in stopwords]
        
        # 빈도 기반 추가
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        frequent = [w for w, f in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]]
        keywords.extend(frequent)
        
        # 중복 제거 및 최대 5개
        return list(dict.fromkeys(keywords))[:5] if keywords else [summary[:30]]
    
    async def _generate_analysis_with_context(self, summary: str, original_text: str) -> Dict[str, Any]:
        """2단계: 요약 + RAG 자료로 분석/조언/인사이트 생성"""
        
        # 관련 문서 검색
        rag_results = self._search_related_documents(summary)
        
        if not self.llm_client:
            logger.warning("LLM 클라이언트가 없어 기본 분석을 반환합니다")
            return {
                "overview": f"회의 요약: {summary}",
                "key_points": ["LLM 분석 불가"],
                "main_topics": ["회의 내용"],
                "decisions": [],
                "action_items": [],
                "insights": ["상세 분석을 위해서는 LLM 설정이 필요합니다"],
                "recommendations": [],
                "related_documents": rag_results
            }
        
        # 최종 분석 프롬프트
        prompt = f"""회의록: {summary}

참고 자료: {rag_results}

다음 내용을 바탕으로 회의 주요 내용에 대해 분석하고, 유사 사례를 바탕으로 조언과 insight를 도출하세요.

다음 JSON 형식으로 응답해주세요:

{{
    "overview": "회의 전체 개요 (2-3문장)",
    "key_points": ["핵심 포인트1", "핵심 포인트2", "핵심 포인트3"],
    "main_topics": ["주요 논의 주제1", "주요 논의 주제2"],
    "decisions": ["결정사항1", "결정사항2"],
    "action_items": ["액션아이템1", "액션아이템2"],
    "insights": ["인사이트1", "인사이트2", "인사이트3"],
    "recommendations": ["권장사항1", "권장사항2"]
}}

참고 자료의 유사 사례를 활용하여 구체적이고 실용적인 조언을 포함해주세요."""
        
        try:
            response = await self.llm_client.invoke_async(
                messages=[{"role": "user", "content": prompt}]
            )
            
            # JSON 파싱 시도
            import json
            result_text = response.strip() if response else ""
            
            try:
                analysis_result = json.loads(result_text)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트를 기본 구조로 변환
                logger.warning("JSON 파싱 실패, 기본 구조로 변환합니다")
                analysis_result = {
                    "overview": result_text,
                    "key_points": [result_text],
                    "main_topics": ["분석 결과"],
                    "decisions": [],
                    "action_items": [],
                    "insights": [result_text],
                    "recommendations": []
                }
            
            # 관련 문서 정보 추가
            analysis_result["related_documents"] = rag_results
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"분석 생성 중 오류: {e}")
            return {
                "overview": "분석 생성 중 오류가 발생했습니다",
                "key_points": ["오류로 인한 분석 실패"],
                "main_topics": [],
                "decisions": [],
                "action_items": [],
                "insights": ["분석 시스템에 문제가 발생했습니다"],
                "recommendations": [],
                "related_documents": rag_results,
                "error": str(e)
            }