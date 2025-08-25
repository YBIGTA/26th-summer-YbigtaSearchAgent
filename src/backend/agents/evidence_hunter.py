"""
증거 수집자 (EvidenceHunter)

RAG 기반으로 관련 증거를 수집하고 출처를 검증합니다.
- 지식베이스 검색
- 출처 검증
- 신뢰도 평가
"""

import json
import logging
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class EvidenceHunter(BaseAgent):
    """RAG 기반 증거 수집 및 출처 검증 전문 에이전트"""
    
    def __init__(self, llm_client=None, retriever=None):
        super().__init__(
            name="EvidenceHunter",
            description="RAG 기반 증거 수집과 출처 검증을 통해 주장을 뒷받침하는 전문가",
            llm_client=llm_client
        )
        self.retriever = retriever  # ChromaIndexManager 등
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        증거 수집 및 검증
        
        Args:
            input_data: {
                "claims": List[Dict],              # ClaimChecker 결과
                "counter_arguments": List[Dict],   # CounterArguer 결과
                "agendas": List[Dict],            # 관련 아젠다
                "search_context": Dict,           # 검색 컨텍스트
                "sources": List[str]              # 검색할 소스 (notion, github, etc.)
            }
            
        Returns:
            {
                "evidence_collection": List[Dict],   # 수집된 증거
                "source_verification": List[Dict],   # 출처 검증 결과
                "credibility_analysis": Dict,        # 신뢰도 분석
                "knowledge_gaps": List[Dict],        # 지식 공백
                "confidence": float                  # 신뢰도
            }
        """
        logger.info("EvidenceHunter: 증거 수집 시작")
        
        try:
            claims = input_data.get("claims", [])
            counter_arguments = input_data.get("counter_arguments", [])
            agendas = input_data.get("agendas", [])
            sources = input_data.get("sources", ["all"])
            
            if not claims:
                return self._empty_result("분석할 주장이 제공되지 않았습니다.")
            
            # 1. 증거 수집 (RAG)
            evidence_collection = await self._collect_evidence(claims, counter_arguments, sources)
            
            # 2. 유사한 회의 사례 검색 (ChromaDB 활용)
            meeting_content = input_data.get("search_context", {}).get("content", "")
            meeting_metadata = input_data.get("search_context", {}).get("meeting_metadata", {})
            similar_meetings = await self.find_similar_meetings(meeting_content, meeting_metadata)
            
            # 유사 회의를 증거로 변환하여 추가
            for meeting in similar_meetings[:5]:  # 최대 5개 유사 회의
                evidence_collection.append({
                    "id": len(evidence_collection) + 1,
                    "related_claim_id": None,  # 전체 회의 관련
                    "evidence_type": "precedent",
                    "content": meeting["content"][:500] + "...",  # 요약본만 포함
                    "source": meeting["source"],
                    "source_type": "similar_meeting",
                    "relevance_score": meeting["similarity_score"],
                    "search_query": "similar_meeting_search",
                    "supports_claim": True,
                    "metadata": {
                        "similar_meeting": True,
                        "meeting_title": meeting["title"],
                        "meeting_date": meeting["meeting_date"],
                        "matched_topic": meeting["matched_topic"],
                        "doc_id": meeting["doc_id"]
                    }
                })
            
            # 3. 출처 검증
            source_verification = await self._verify_sources(evidence_collection)
            
            # 4. 신뢰도 분석
            credibility_analysis = await self._analyze_credibility(evidence_collection, source_verification)
            
            # 5. 지식 공백 식별
            knowledge_gaps = await self._identify_knowledge_gaps(claims, evidence_collection)
            
            # 6. 신뢰도 계산
            confidence = self._calculate_confidence(evidence_collection, source_verification)
            
            result = {
                "evidence_collection": evidence_collection,
                "source_verification": source_verification,
                "credibility_analysis": credibility_analysis,
                "knowledge_gaps": knowledge_gaps,
                "similar_meetings": similar_meetings,  # 유사 회의 정보 추가
                "confidence": confidence,
                "agent": self.name,
                "timestamp": input_data.get("timestamp")
            }
            
            similar_count = len(similar_meetings)
            total_evidence = len(evidence_collection)
            logger.info(f"EvidenceHunter: {total_evidence}개 증거 수집 완료 (유사 회의 {similar_count}개 포함)")
            return result
            
        except Exception as e:
            logger.error(f"EvidenceHunter 처리 오류: {str(e)}")
            return self._empty_result(str(e))
    
    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """빈 결과 반환"""
        return {
            "error": error_msg,
            "evidence_collection": [],
            "source_verification": [],
            "credibility_analysis": {},
            "knowledge_gaps": [],
            "similar_meetings": [],
            "confidence": 0.0
        }
    
    async def _collect_evidence(self, claims: List[Dict], counter_arguments: List[Dict], sources: List[str]) -> List[Dict]:
        """ChromaDB 기반 증거 수집 - 유사한 회의 사례 검색 포함"""
        
        evidence_collection = []
        
        # 각 주장에 대해 증거 검색
        for claim in claims[:5]:  # 최대 5개 주장
            claim_id = claim.get("id")
            claim_text = claim.get("claim", "")
            
            if not claim_text:
                continue
                
            # RAG 검색 쿼리 생성
            search_queries = await self._generate_search_queries(claim)
            
            for query in search_queries[:3]:  # 최대 3개 쿼리
                # ChromaDB 기반 RAG 검색
                search_results = await self._perform_rag_search(query, sources)
                
                # 검색 결과를 증거로 변환
                for result in search_results:
                    # 증거 유형 자동 판단
                    evidence_type = self._determine_evidence_type(result)
                    
                    # 주장 지지도 계산
                    supports_claim = await self._analyze_claim_support(claim_text, result.get("content", ""))
                    
                    evidence_collection.append({
                        "id": len(evidence_collection) + 1,
                        "related_claim_id": claim_id,
                        "evidence_type": evidence_type,
                        "content": result.get("content", ""),
                        "source": result.get("source", ""),
                        "source_type": result.get("source_type", "unknown"),
                        "relevance_score": result.get("relevance_score", 0.0),
                        "search_query": query,
                        "supports_claim": supports_claim,
                        "metadata": result.get("metadata", {})
                    })
        
        logger.info(f"ChromaDB에서 총 {len(evidence_collection)}개 증거 수집 완료")
        return evidence_collection[:20]  # 최대 20개 증거
    
    async def _generate_search_queries(self, claim: Dict[str, Any]) -> List[str]:
        """주장을 바탕으로 검색 쿼리 생성"""
        
        claim_text = claim.get("claim", "")
        claim_type = claim.get("type", "")
        
        context = f"""
주장: {claim_text}
주장 유형: {claim_type}
"""
        
        question = """
이 주장을 뒷받침하거나 반박할 수 있는 증거를 찾기 위한 검색 쿼리를 생성하세요:

{
    "search_queries": [
        "구체적인 검색어 1",
        "구체적인 검색어 2", 
        "구체적인 검색어 3"
    ]
}

효과적인 검색을 위해:
1. 핵심 키워드 추출
2. 동의어 및 관련 용어 포함
3. 다양한 관점에서 접근
4. 구체적이고 명확한 표현 사용
"""
        
        response = await self.think(context, question)
        
        try:
            if response.startswith("```json"):
                response = response.strip("```json").strip("```").strip()
            
            result = json.loads(response)
            return result.get("search_queries", [claim_text])
            
        except json.JSONDecodeError:
            # 기본 쿼리 반환
            return [claim_text, claim_text.split()[0] if claim_text.split() else ""]
    
    async def _perform_rag_search(self, query: str, sources: List[str]) -> List[Dict]:
        """실제 RAG 검색 수행"""
        
        if not self.retriever:
            # 시뮬레이션 결과 반환
            return [
                {
                    "content": f"'{query}'에 대한 검색 결과 (시뮬레이션)",
                    "source": "simulation_source",
                    "source_type": "document", 
                    "relevance_score": 0.8,
                    "metadata": {"simulated": True}
                }
            ]
        
        try:
            # 실제 ChromaDB 검색
            search_results = []
            
            # 소스별 검색
            for source in sources:
                if source == "all":
                    results = await self._search_all_sources(query)
                else:
                    results = await self._search_specific_source(query, source)
                
                search_results.extend(results)
            
            # 관련도 순으로 정렬
            search_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            return search_results[:10]  # 상위 10개
            
        except Exception as e:
            logger.error(f"RAG 검색 오류: {str(e)}")
            return []
    
    async def _search_all_sources(self, query: str) -> List[Dict]:
        """모든 소스에서 검색 - ChromaDB 하이브리드 검색 사용"""
        if not self.retriever:
            return []
            
        try:
            # ChromaDB 하이브리드 검색 수행
            search_results = self.retriever.hybrid_search(
                query=query,
                top_k=10,  # 충분한 결과 가져오기
                vector_weight=0.7  # 벡터 검색 가중치
            )
            
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "content": result.get("content", ""),
                    "source": result.get("metadata", {}).get("source", "chroma_db"),
                    "source_type": "document",
                    "relevance_score": min(1.0, result.get("score", 0.0) * 2),  # 점수 정규화
                    "metadata": {
                        "doc_id": result.get("metadata", {}).get("doc_id"),
                        "title": result.get("metadata", {}).get("title", "Unknown"),
                        "indexed_at": result.get("metadata", {}).get("indexed_at"),
                        "chunk_index": result.get("metadata", {}).get("chunk_index", 0)
                    }
                })
            
            logger.info(f"ChromaDB에서 {len(formatted_results)}개 유사 문서 검색 완료")
            return formatted_results
            
        except Exception as e:
            logger.error(f"ChromaDB 검색 오류: {str(e)}")
            return []
    
    async def _search_specific_source(self, query: str, source: str) -> List[Dict]:
        """특정 소스에서 검색 - ChromaDB 필터 검색 사용"""
        if not self.retriever:
            return []
            
        try:
            # 소스별 필터 설정
            source_filter = {"source": source} if source != "all" else None
            
            # ChromaDB 하이브리드 검색 (필터 적용)
            search_results = self.retriever.hybrid_search(
                query=query,
                top_k=8,
                filter=source_filter,
                vector_weight=0.8  # 특정 소스 검색시 벡터 검색 가중치 높임
            )
            
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "content": result.get("content", ""),
                    "source": result.get("metadata", {}).get("source", source),
                    "source_type": "document",
                    "relevance_score": min(1.0, result.get("score", 0.0) * 2),  # 점수 정규화
                    "metadata": {
                        "doc_id": result.get("metadata", {}).get("doc_id"),
                        "title": result.get("metadata", {}).get("title", "Unknown"),
                        "indexed_at": result.get("metadata", {}).get("indexed_at"),
                        "chunk_index": result.get("metadata", {}).get("chunk_index", 0),
                        "filtered_source": source
                    }
                })
            
            logger.info(f"{source} 소스에서 {len(formatted_results)}개 유사 문서 검색 완료")
            return formatted_results
            
        except Exception as e:
            logger.error(f"{source} 소스 검색 오류: {str(e)}")
            return []
    
    async def _verify_sources(self, evidence_collection: List[Dict]) -> List[Dict]:
        """출처 검증"""
        
        verification_results = []
        
        for evidence in evidence_collection:
            source = evidence.get("source", "")
            source_type = evidence.get("source_type", "unknown")
            
            # 출처별 신뢰도 평가
            credibility_score = self._evaluate_source_credibility(source, source_type)
            
            # 출처 검증 결과
            verification = {
                "evidence_id": evidence.get("id"),
                "source": source,
                "source_type": source_type,
                "credibility_score": credibility_score,
                "verification_status": "verified" if credibility_score > 0.7 else "questionable" if credibility_score > 0.3 else "unreliable",
                "authority_level": self._assess_authority_level(source, source_type),
                "recency": self._assess_recency(evidence.get("metadata", {})),
                "bias_risk": self._assess_bias_risk(source, source_type),
                "recommendations": []
            }
            
            # 추천사항 추가
            if credibility_score < 0.5:
                verification["recommendations"].append("추가 출처 확인 필요")
            if verification["bias_risk"] == "high":
                verification["recommendations"].append("편향 가능성 주의")
                
            verification_results.append(verification)
        
        return verification_results
    
    def _evaluate_source_credibility(self, source: str, source_type: str) -> float:
        """출처 신뢰도 평가"""
        
        base_score = 0.5
        
        # 소스 타입별 기본 점수
        type_scores = {
            "academic": 0.9,
            "official": 0.8,
            "news": 0.7,
            "blog": 0.4,
            "wiki": 0.6,
            "document": 0.7,
            "unknown": 0.3
        }
        
        base_score = type_scores.get(source_type, 0.3)
        
        # 소스별 추가 평가
        if "notion" in source.lower():
            base_score = min(base_score + 0.1, 1.0)  # 내부 문서는 약간 가점
        elif "github" in source.lower():
            base_score = min(base_score + 0.05, 1.0)
        elif "similar_meeting" in source_type:
            base_score = min(base_score + 0.15, 1.0)  # 유사 회의는 높은 신뢰도
            
        return base_score
    
    def _assess_authority_level(self, source: str, source_type: str) -> str:
        """권위 수준 평가"""
        
        if source_type in ["academic", "official", "similar_meeting"]:
            return "high"
        elif source_type in ["news", "document"]:
            return "medium"
        else:
            return "low"
    
    def _assess_recency(self, metadata: Dict) -> str:
        """최신성 평가"""
        
        # 메타데이터에서 날짜 정보 확인
        created_at = metadata.get("created_at")
        updated_at = metadata.get("updated_at")
        
        if not created_at and not updated_at:
            return "unknown"
        
        # TODO: 실제 날짜 비교 구현
        return "recent"  # 임시
    
    def _assess_bias_risk(self, source: str, source_type: str) -> str:
        """편향 위험 평가"""
        
        if source_type == "blog":
            return "high"
        elif source_type in ["news", "wiki"]:
            return "medium"
        else:
            return "low"
    
    async def _analyze_credibility(self, evidence_collection: List[Dict], source_verification: List[Dict]) -> Dict[str, Any]:
        """신뢰도 종합 분석"""
        
        if not evidence_collection:
            return {
                "overall_credibility": 0.0,
                "source_distribution": {},
                "verification_summary": {},
                "recommendations": []
            }
        
        # 전체 신뢰도 점수
        credibility_scores = [v.get("credibility_score", 0) for v in source_verification]
        overall_credibility = sum(credibility_scores) / len(credibility_scores) if credibility_scores else 0.0
        
        # 출처별 분포
        source_distribution = {}
        for evidence in evidence_collection:
            source_type = evidence.get("source_type", "unknown")
            source_distribution[source_type] = source_distribution.get(source_type, 0) + 1
        
        # 검증 상태 요약
        verification_summary = {}
        for verification in source_verification:
            status = verification.get("verification_status", "unknown")
            verification_summary[status] = verification_summary.get(status, 0) + 1
        
        # 추천사항
        recommendations = []
        if overall_credibility < 0.6:
            recommendations.append("출처의 전반적인 신뢰도가 낮습니다")
        
        reliable_count = verification_summary.get("verified", 0)
        total_count = len(source_verification)
        if reliable_count / max(total_count, 1) < 0.7:
            recommendations.append("신뢰할 수 있는 출처의 비율을 높여야 합니다")
        
        return {
            "overall_credibility": round(overall_credibility, 2),
            "source_distribution": source_distribution,
            "verification_summary": verification_summary,
            "recommendations": recommendations
        }
    
    async def _identify_knowledge_gaps(self, claims: List[Dict], evidence_collection: List[Dict]) -> List[Dict]:
        """지식 공백 식별"""
        
        knowledge_gaps = []
        
        # 각 주장별 증거 충분성 검사
        for claim in claims:
            claim_id = claim.get("id")
            claim_text = claim.get("claim", "")
            
            # 해당 주장에 대한 증거 수집
            related_evidence = [e for e in evidence_collection if e.get("related_claim_id") == claim_id]
            
            if len(related_evidence) < 2:  # 증거가 부족한 경우
                knowledge_gaps.append({
                    "gap_id": len(knowledge_gaps) + 1,
                    "related_claim_id": claim_id,
                    "gap_type": "insufficient_evidence",
                    "description": f"'{claim_text}' 주장에 대한 증거가 부족합니다",
                    "severity": "high" if len(related_evidence) == 0 else "medium",
                    "suggested_searches": [
                        f"{claim_text} 관련 데이터",
                        f"{claim_text} 사례 연구",
                        f"{claim_text} 전문가 의견"
                    ],
                    "impact": "주장의 신뢰도가 낮아질 수 있습니다"
                })
        
        return knowledge_gaps
    
    def _calculate_confidence(self, evidence_collection: List[Dict], source_verification: List[Dict]) -> float:
        """신뢰도 계산"""
        
        if not evidence_collection:
            return 0.0
        
        # 기본 신뢰도
        confidence = 0.3
        
        # 증거 수량
        evidence_count = len(evidence_collection)
        confidence += min(evidence_count / 10, 0.3)  # 최대 0.3 추가
        
        # 출처 신뢰도
        if source_verification:
            avg_credibility = sum(v.get("credibility_score", 0) for v in source_verification) / len(source_verification)
            confidence += avg_credibility * 0.3
        
        # 출처 다양성
        source_types = set(e.get("source_type") for e in evidence_collection)
        if len(source_types) > 2:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _determine_evidence_type(self, result: Dict) -> str:
        """검색 결과에서 증거 유형을 자동 판단"""
        content = result.get("content", "").lower()
        metadata = result.get("metadata", {})
        source = result.get("source", "").lower()
        
        # 소스 기반 판단
        if "github" in source:
            return "data"
        elif "notion" in source:
            return "document"
        elif metadata.get("title", "").lower().find("회의") >= 0:
            return "precedent"
        
        # 내용 기반 판단
        if any(keyword in content for keyword in ["데이터", "수치", "통계", "결과"]):
            return "data"
        elif any(keyword in content for keyword in ["전문가", "의견", "견해", "판단"]):
            return "expert_opinion"  
        elif any(keyword in content for keyword in ["사례", "경험", "과거", "이전"]):
            return "precedent"
        else:
            return "document"
    
    async def _analyze_claim_support(self, claim: str, evidence_content: str) -> bool:
        """증거가 주장을 지지하는지 분석"""
        if not evidence_content or len(evidence_content.strip()) < 10:
            return False
            
        try:
            context = f"""
주장: {claim}
증거: {evidence_content[:500]}...
"""
            
            question = """
이 증거가 주어진 주장을 지지하거나 뒷받침하는지 분석하세요:

{
    "supports_claim": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "분석 근거"
}

증거와 주장 간의 관련성과 일치도를 고려하여 판단하세요.
"""
            
            response = await self.think(context, question)
            
            # JSON 파싱 시도
            result = self.parse_json_response(response)
            if result and "supports_claim" in result:
                return result.get("supports_claim", False)
                
        except Exception as e:
            logger.error(f"주장 지지도 분석 오류: {str(e)}")
        
        # 기본값: 검색된 증거는 관련성이 있다고 가정
        return True
    
    async def find_similar_meetings(self, meeting_content: str, meeting_metadata: Dict = None) -> List[Dict]:
        """
        유사한 회의 사례 검색 - ChromaDB를 활용한 의미론적 유사도 검색
        
        Args:
            meeting_content: 현재 회의 내용
            meeting_metadata: 회의 메타데이터 (날짜, 참석자 등)
            
        Returns:
            유사한 회의 목록과 관련도 점수
        """
        if not self.retriever:
            logger.warning("ChromaDB retriever가 없어 유사 회의 검색을 건너뜁니다.")
            return []
        
        try:
            # 회의 내용에서 핵심 키워드 추출
            key_topics = await self._extract_meeting_topics(meeting_content)
            
            similar_meetings = []
            
            # 각 핵심 주제별로 유사 회의 검색
            for topic in key_topics[:3]:  # 상위 3개 주제만 사용
                search_results = self.retriever.hybrid_search(
                    query=topic,
                    top_k=5,
                    filter=None,  # 모든 소스에서 검색
                    vector_weight=0.8  # 의미론적 유사도 중시
                )
                
                for result in search_results:
                    # 현재 회의와의 중복 방지
                    doc_metadata = result.get("metadata", {})
                    if self._is_same_meeting(meeting_metadata, doc_metadata):
                        continue
                        
                    similar_meetings.append({
                        "content": result.get("content", ""),
                        "source": result.get("metadata", {}).get("source", "unknown"),
                        "title": result.get("metadata", {}).get("title", "Unknown Meeting"),
                        "doc_id": result.get("metadata", {}).get("doc_id"),
                        "similarity_score": result.get("score", 0.0),
                        "matched_topic": topic,
                        "meeting_date": doc_metadata.get("created_at", "unknown"),
                        "metadata": doc_metadata
                    })
            
            # 중복 제거 및 점수순 정렬
            unique_meetings = self._deduplicate_meetings(similar_meetings)
            unique_meetings.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            logger.info(f"유사한 회의 {len(unique_meetings)}개 발견")
            return unique_meetings[:10]  # 상위 10개만 반환
            
        except Exception as e:
            logger.error(f"유사 회의 검색 오류: {str(e)}")
            return []
    
    async def _extract_meeting_topics(self, content: str) -> List[str]:
        """회의 내용에서 핵심 주제 추출"""
        try:
            context = f"회의 내용: {content[:1000]}..."  # 첫 1000자만 사용
            
            question = """
이 회의 내용에서 핵심 주제와 키워드를 추출하세요:

{
    "key_topics": [
        "핵심 주제 1",
        "핵심 주제 2", 
        "핵심 주제 3",
        "핵심 주제 4",
        "핵심 주제 5"
    ]
}

회의의 주요 안건, 논의사항, 결정사항 등을 중심으로 추출하세요.
"""
            
            response = await self.think(context, question)
            result = self.parse_json_response(response)
            
            if result and "key_topics" in result:
                return result["key_topics"][:5]  # 최대 5개
                
        except Exception as e:
            logger.error(f"주제 추출 오류: {str(e)}")
        
        # 기본값: 내용의 첫 100자를 사용
        return [content[:100]] if content else ["회의"]
    
    def _is_same_meeting(self, current_metadata: Dict, candidate_metadata: Dict) -> bool:
        """두 회의가 동일한지 확인"""
        if not current_metadata or not candidate_metadata:
            return False
        
        # 제목이나 ID로 동일성 확인
        current_title = current_metadata.get("title", "")
        candidate_title = candidate_metadata.get("title", "")
        
        if current_title and candidate_title and current_title == candidate_title:
            return True
            
        # 날짜와 시간으로 확인
        current_date = current_metadata.get("timestamp") or current_metadata.get("created_at")
        candidate_date = candidate_metadata.get("indexed_at") or candidate_metadata.get("created_at")
        
        if current_date and candidate_date:
            # 같은 날짜면 동일한 회의로 간주
            return current_date[:10] == candidate_date[:10]
        
        return False
    
    def _deduplicate_meetings(self, meetings: List[Dict]) -> List[Dict]:
        """중복 회의 제거"""
        seen_ids = set()
        unique_meetings = []
        
        for meeting in meetings:
            doc_id = meeting.get("doc_id")
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_meetings.append(meeting)
            elif not doc_id:  # doc_id가 없는 경우 제목으로 중복 확인
                title = meeting.get("title", "")
                if title not in seen_ids:
                    seen_ids.add(title)
                    unique_meetings.append(meeting)
        
        return unique_meetings
    
    async def search_and_verify(self, content: str, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        검색 및 검증 (파이프라인 호환용 래퍼 메서드)
        
        Args:
            content: 회의 내용 텍스트
            meeting_data: 전체 회의 데이터
            
        Returns:
            증거 수집 및 검증 결과
        """
        # meeting_data에서 claims, counter_arguments 등을 추출하거나 기본값 사용
        input_data = {
            "claims": meeting_data.get("claims", []),
            "counter_arguments": meeting_data.get("counter_arguments", []),
            "agendas": meeting_data.get("agendas", []),
            "search_context": {
                "content": content,
                "meeting_metadata": meeting_data.get("metadata", {})
            },
            "sources": ["all"],
            "timestamp": meeting_data.get("timestamp")
        }
        
        # 만약 claims가 없다면 content를 기반으로 기본 claim 생성
        if not input_data["claims"] and content:
            input_data["claims"] = [
                {
                    "id": 1,
                    "claim": content[:200] + "..." if len(content) > 200 else content,
                    "type": "general_discussion",
                    "confidence": 0.8
                }
            ]
        
        return await self.process(input_data)