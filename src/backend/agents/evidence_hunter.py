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
            
            # 2. 출처 검증
            source_verification = await self._verify_sources(evidence_collection)
            
            # 3. 신뢰도 분석
            credibility_analysis = await self._analyze_credibility(evidence_collection, source_verification)
            
            # 4. 지식 공백 식별
            knowledge_gaps = await self._identify_knowledge_gaps(claims, evidence_collection)
            
            # 5. 신뢰도 계산
            confidence = self._calculate_confidence(evidence_collection, source_verification)
            
            result = {
                "evidence_collection": evidence_collection,
                "source_verification": source_verification,
                "credibility_analysis": credibility_analysis,
                "knowledge_gaps": knowledge_gaps,
                "confidence": confidence,
                "agent": self.name,
                "timestamp": input_data.get("timestamp")
            }
            
            logger.info(f"EvidenceHunter: {len(evidence_collection)}개 증거 수집 완료")
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
            "confidence": 0.0
        }
    
    async def _collect_evidence(self, claims: List[Dict], counter_arguments: List[Dict], sources: List[str]) -> List[Dict]:
        """RAG 기반 증거 수집"""
        
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
                # 실제 RAG 검색 (시뮬레이션)
                search_results = await self._perform_rag_search(query, sources)
                
                # 검색 결과를 증거로 변환
                for result in search_results:
                    evidence_collection.append({
                        "id": len(evidence_collection) + 1,
                        "related_claim_id": claim_id,
                        "evidence_type": "document|data|precedent|expert_opinion",
                        "content": result.get("content", ""),
                        "source": result.get("source", ""),
                        "source_type": result.get("source_type", "unknown"),
                        "relevance_score": result.get("relevance_score", 0.0),
                        "search_query": query,
                        "supports_claim": True,  # 추후 분석으로 결정
                        "metadata": result.get("metadata", {})
                    })
        
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
        """모든 소스에서 검색"""
        # TODO: 실제 ChromaDB 검색 구현
        return []
    
    async def _search_specific_source(self, query: str, source: str) -> List[Dict]:
        """특정 소스에서 검색"""
        # TODO: 소스별 검색 구현
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
            
        return base_score
    
    def _assess_authority_level(self, source: str, source_type: str) -> str:
        """권위 수준 평가"""
        
        if source_type in ["academic", "official"]:
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