"""
주장 검증자 (ClaimChecker)

회의 발화에서 주장-근거-반례 구조를 분석합니다.
- 논리 구조 분석
- 근거의 타당성 검증
- 논리 오류 탐지
"""

import json
import logging
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ClaimChecker(BaseAgent):
    """주장-근거 구조 분석 전문 에이전트"""
    
    def __init__(self, llm_client=None):
        super().__init__(
            name="ClaimChecker", 
            description="주장-근거-반례 구조를 분석하고 논리 오류를 탐지하는 전문가",
            llm_client=llm_client
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        주장-근거 구조 분석
        
        Args:
            input_data: {
                "transcript": str,      # 회의록 전문
                "agendas": List[Dict],  # AgendaMiner 결과
                "speakers": List[str],  # 발화자 목록
                "timeline": List[Dict]  # 타임라인 정보
            }
            
        Returns:
            {
                "claims": List[Dict],           # 주장 분석
                "logical_structure": Dict,      # 논리 구조
                "fallacies": List[Dict],        # 논리 오류
                "evidence_quality": Dict,       # 근거 품질 평가
                "confidence": float             # 신뢰도
            }
        """
        logger.info("ClaimChecker: 주장-근거 구조 분석 시작")
        
        try:
            transcript = input_data.get("transcript", "")
            agendas = input_data.get("agendas", [])
            speakers = input_data.get("speakers", [])
            timeline = input_data.get("timeline", [])
            
            if not transcript:
                return self._empty_result("회의록이 제공되지 않았습니다.")
            
            # 1. 주장 추출 및 분석
            claims = await self._extract_claims(transcript, speakers, timeline)
            
            # 2. 논리 구조 분석
            logical_structure = await self._analyze_logical_structure(claims, agendas)
            
            # 3. 논리 오류 탐지
            fallacies = await self._detect_fallacies(claims, transcript)
            
            # 4. 근거 품질 평가
            evidence_quality = await self._evaluate_evidence_quality(claims)
            
            # 5. 신뢰도 계산
            confidence = self._calculate_confidence(claims, fallacies, evidence_quality)
            
            result = {
                "claims": claims,
                "logical_structure": logical_structure,
                "fallacies": fallacies,
                "evidence_quality": evidence_quality,
                "confidence": confidence,
                "agent": self.name,
                "timestamp": input_data.get("timestamp")
            }
            
            logger.info(f"ClaimChecker: {len(claims)}개 주장 분석 완료")
            return result
            
        except Exception as e:
            logger.error(f"ClaimChecker 처리 오류: {str(e)}")
            return self._empty_result(str(e))
    
    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """빈 결과 반환"""
        return {
            "error": error_msg,
            "claims": [],
            "logical_structure": {},
            "fallacies": [],
            "evidence_quality": {},
            "confidence": 0.0
        }
    
    async def _extract_claims(self, transcript: str, speakers: List[str], timeline: List[Dict]) -> List[Dict]:
        """주장 추출 및 분석"""
        
        context = f"""
회의록:
{transcript[:2500]}...

참석자: {', '.join(speakers) if speakers else '정보 없음'}
"""
        
        question = "이 회의록에서 참석자들이 제시한 주장들을 분석하여 JSON 형식으로 반환하세요. 명시적인 주장과 암묵적인 주장을 모두 포함하고, 제시된 근거의 유형과 강도를 평가하세요."
        
        # 기대하는 형식 정의
        expected_format = {
            "claims": [
                {
                    "id": 1,
                    "speaker": "발화자명",
                    "claim": "주장 내용",
                    "type": "fact",
                    "confidence_level": "high",
                    "evidence": [
                        {
                            "type": "data",
                            "content": "근거 내용",
                            "strength": "strong"
                        }
                    ],
                    "context": "주장이 나온 맥락",
                    "implications": ["함의1", "함의2"],
                    "related_claims": [2, 3],
                    "time_reference": "발언 시점 추정"
                }
            ]
        }
        
        try:
            result = await self.think_structured(context, question, expected_format)
            claims = result.get("claims", [])
            
            # 결과 검증 및 보정
            validated_claims = []
            valid_types = ["fact", "opinion", "proposal", "objection"]
            valid_confidence_levels = ["high", "medium", "low"]
            valid_evidence_types = ["data", "example", "authority", "logic"]
            valid_strengths = ["strong", "moderate", "weak"]
            
            for i, claim in enumerate(claims):
                if isinstance(claim, dict):
                    # evidence 검증
                    validated_evidence = []
                    for evidence in claim.get("evidence", []):
                        if isinstance(evidence, dict):
                            validated_evidence.append({
                                "type": evidence.get("type", "logic") if evidence.get("type") in valid_evidence_types else "logic",
                                "content": str(evidence.get("content", "")).strip(),
                                "strength": evidence.get("strength", "weak") if evidence.get("strength") in valid_strengths else "weak"
                            })
                    
                    validated_claim = {
                        "id": claim.get("id", i + 1),
                        "speaker": str(claim.get("speaker", "알 수 없음")).strip(),
                        "claim": str(claim.get("claim", "")).strip(),
                        "type": claim.get("type", "opinion") if claim.get("type") in valid_types else "opinion",
                        "confidence_level": claim.get("confidence_level", "medium") if claim.get("confidence_level") in valid_confidence_levels else "medium",
                        "evidence": validated_evidence[:5],  # 최대 5개
                        "context": str(claim.get("context", "")).strip(),
                        "implications": claim.get("implications", [])[:5],  # 최대 5개
                        "related_claims": claim.get("related_claims", [])[:5],  # 최대 5개
                        "time_reference": str(claim.get("time_reference", "")).strip()
                    }
                    validated_claims.append(validated_claim)
            
            return validated_claims
            
        except Exception as e:
            logger.warning(f"ClaimChecker: 주장 추출 오류 - {str(e)}")
            return []
    
    async def _analyze_logical_structure(self, claims: List[Dict], agendas: List[Dict]) -> Dict[str, Any]:
        """논리 구조 분석"""
        
        claims_str = json.dumps(claims[:5], ensure_ascii=False, indent=2)  # 최대 5개만
        agendas_str = json.dumps(agendas[:3], ensure_ascii=False, indent=2)  # 최대 3개만
        
        context = f"""
분석된 주장들:
{claims_str}

관련 아젠다:
{agendas_str}
"""
        
        question = """
주장들 간의 논리적 관계와 구조를 분석하세요:

{
    "argument_chains": [
        {
            "id": 1,
            "premise_claims": [1, 2],
            "conclusion_claim": 3,
            "logical_validity": "valid|invalid|uncertain",
            "chain_strength": "strong|moderate|weak"
        }
    ],
    "conflict_analysis": [
        {
            "conflicting_claims": [1, 4],
            "conflict_type": "direct|indirect|perspective",
            "resolution_needed": true,
            "synthesis_possible": false
        }
    ],
    "consensus_areas": [
        {
            "topic": "합의 영역",
            "supporting_claims": [1, 2, 3],
            "consensus_strength": "strong|partial|weak"
        }
    ],
    "gaps": [
        {
            "missing_element": "부족한 요소",
            "impact": "high|medium|low",
            "suggestion": "보완 제안"
        }
    ]
}
"""
        
        response = await self.think(context, question)
        
        try:
            if response.startswith("```json"):
                response = response.strip("```json").strip("```").strip()
            
            return json.loads(response)
            
        except json.JSONDecodeError:
            return {
                "argument_chains": [],
                "conflict_analysis": [],
                "consensus_areas": [],
                "gaps": []
            }
    
    async def _detect_fallacies(self, claims: List[Dict], transcript: str) -> List[Dict]:
        """논리 오류 탐지"""
        
        claims_str = json.dumps(claims[:5], ensure_ascii=False, indent=2)
        
        context = f"""
분석된 주장들:
{claims_str}

원본 텍스트 샘플:
{transcript[:1500]}...
"""
        
        question = """
이 주장들에서 논리적 오류(logical fallacies)를 탐지하세요:

{
    "fallacies": [
        {
            "id": 1,
            "type": "ad_hominem|strawman|false_dichotomy|appeal_to_authority|hasty_generalization|circular_reasoning|slippery_slope|other",
            "related_claim_id": 2,
            "description": "오류 설명",
            "problematic_text": "문제가 되는 발언",
            "severity": "high|medium|low",
            "correction_suggestion": "수정 제안"
        }
    ]
}

주요 논리 오류 유형:
- ad_hominem: 인신공격
- strawman: 허수아비 공격
- false_dichotomy: 거짓 이분법
- appeal_to_authority: 권위에의 호소
- hasty_generalization: 성급한 일반화
- circular_reasoning: 순환논리
- slippery_slope: 미끄러운 경사
"""
        
        response = await self.think(context, question)
        
        try:
            if response.startswith("```json"):
                response = response.strip("```json").strip("```").strip()
            
            result = json.loads(response)
            return result.get("fallacies", [])
            
        except json.JSONDecodeError:
            return []
    
    async def _evaluate_evidence_quality(self, claims: List[Dict]) -> Dict[str, Any]:
        """근거 품질 평가"""
        
        total_claims = len(claims)
        total_evidence = sum(len(claim.get("evidence", [])) for claim in claims)
        
        if total_claims == 0:
            return {
                "overall_score": 0.0,
                "evidence_count": 0,
                "evidence_types": {},
                "strength_distribution": {},
                "recommendations": []
            }
        
        # 근거 유형별 분포
        evidence_types = {}
        strength_distribution = {"strong": 0, "moderate": 0, "weak": 0}
        
        for claim in claims:
            for evidence in claim.get("evidence", []):
                ev_type = evidence.get("type", "unknown")
                ev_strength = evidence.get("strength", "weak")
                
                evidence_types[ev_type] = evidence_types.get(ev_type, 0) + 1
                strength_distribution[ev_strength] = strength_distribution.get(ev_strength, 0) + 1
        
        # 전체 점수 계산
        strong_ratio = strength_distribution["strong"] / max(total_evidence, 1)
        evidence_per_claim = total_evidence / total_claims
        
        overall_score = min((strong_ratio * 0.5 + min(evidence_per_claim / 2, 1) * 0.5), 1.0)
        
        # 개선 제안
        recommendations = []
        if evidence_per_claim < 1:
            recommendations.append("주장에 대한 근거 제시가 부족합니다")
        if strong_ratio < 0.3:
            recommendations.append("보다 강력한 근거가 필요합니다")
        if "data" not in evidence_types:
            recommendations.append("데이터 기반 근거를 추가하면 좋겠습니다")
        
        return {
            "overall_score": round(overall_score, 2),
            "evidence_count": total_evidence,
            "evidence_types": evidence_types,
            "strength_distribution": strength_distribution,
            "recommendations": recommendations
        }
    
    def _calculate_confidence(self, claims: List[Dict], fallacies: List[Dict], evidence_quality: Dict) -> float:
        """신뢰도 계산"""
        
        if not claims:
            return 0.0
        
        # 기본 신뢰도
        confidence = 0.4
        
        # 주장 수에 따른 보정
        if len(claims) >= 2:
            confidence += 0.2
            
        # 근거 품질에 따른 보정
        evidence_score = evidence_quality.get("overall_score", 0.0)
        confidence += evidence_score * 0.3
        
        # 논리 오류에 따른 패널티
        high_severity_fallacies = len([f for f in fallacies if f.get("severity") == "high"])
        confidence -= high_severity_fallacies * 0.1
        
        # 근거가 있는 주장 비율
        claims_with_evidence = len([c for c in claims if c.get("evidence")])
        if claims:
            evidence_ratio = claims_with_evidence / len(claims)
            confidence += evidence_ratio * 0.1
        
        return max(0.0, min(confidence, 1.0))