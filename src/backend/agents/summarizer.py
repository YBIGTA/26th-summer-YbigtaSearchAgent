"""
요약자 (Summarizer)

모든 에이전트의 분석 결과를 종합하여 보고서를 생성합니다.
- 결론 도출
- 액션 아이템 추출
- 보고서 생성
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Summarizer(BaseAgent):
    """결론 도출 및 보고서 생성 전문 에이전트"""
    
    def __init__(self, llm_client=None):
        super().__init__(
            name="Summarizer",
            description="모든 분석 결과를 종합하여 결론을 도출하고 실행 가능한 보고서를 생성하는 전문가",
            llm_client=llm_client
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        종합 분석 및 보고서 생성
        
        Args:
            input_data: {
                "agenda_results": Dict,           # AgendaMiner 결과
                "claim_results": Dict,            # ClaimChecker 결과
                "counter_results": Dict,          # CounterArguer 결과
                "evidence_results": Dict,         # EvidenceHunter 결과
                "meeting_metadata": Dict,         # 회의 메타데이터
                "original_transcript": str        # 원본 회의록
            }
            
        Returns:
            {
                "executive_summary": Dict,        # 경영진 요약
                "detailed_analysis": Dict,        # 상세 분석
                "action_items": List[Dict],       # 액션 아이템
                "recommendations": List[Dict],    # 권고사항
                "risk_assessment": Dict,          # 리스크 평가
                "follow_up": Dict,               # 후속 조치
                "report_metadata": Dict,          # 보고서 메타데이터
                "confidence": float               # 신뢰도
            }
        """
        logger.info("Summarizer: 종합 분석 및 보고서 생성 시작")
        
        try:
            agenda_results = input_data.get("agenda_results", {})
            claim_results = input_data.get("claim_results", {})
            counter_results = input_data.get("counter_results", {})
            evidence_results = input_data.get("evidence_results", {})
            meeting_metadata = input_data.get("meeting_metadata", {})
            original_transcript = input_data.get("original_transcript", "")
            
            # 1. 경영진 요약 생성
            executive_summary = await self._generate_executive_summary(
                agenda_results, claim_results, counter_results, evidence_results, meeting_metadata
            )
            
            # 2. 상세 분석 정리
            detailed_analysis = await self._create_detailed_analysis(
                agenda_results, claim_results, counter_results, evidence_results
            )
            
            # 3. 액션 아이템 추출
            action_items = await self._extract_action_items(
                agenda_results, claim_results, counter_results
            )
            
            # 4. 권고사항 생성
            recommendations = await self._generate_recommendations(
                claim_results, counter_results, evidence_results
            )
            
            # 5. 리스크 평가
            risk_assessment = await self._assess_overall_risks(
                counter_results, evidence_results, claim_results
            )
            
            # 6. 후속 조치 계획
            follow_up = await self._plan_follow_up(action_items, recommendations, risk_assessment)
            
            # 7. 신뢰도 계산
            confidence = self._calculate_confidence(
                agenda_results, claim_results, evidence_results, counter_results
            )
            
            # 8. 보고서 메타데이터
            report_metadata = self._create_report_metadata(meeting_metadata, confidence)
            
            result = {
                "executive_summary": executive_summary,
                "detailed_analysis": detailed_analysis,
                "action_items": action_items,
                "recommendations": recommendations,
                "risk_assessment": risk_assessment,
                "follow_up": follow_up,
                "report_metadata": report_metadata,
                "confidence": confidence,
                "agent": self.name,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Summarizer: 보고서 생성 완료 (신뢰도: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Summarizer 처리 오류: {str(e)}")
            return self._empty_result(str(e))
    
    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """빈 결과 반환"""
        return {
            "error": error_msg,
            "executive_summary": {},
            "detailed_analysis": {},
            "action_items": [],
            "recommendations": [],
            "risk_assessment": {},
            "follow_up": {},
            "report_metadata": {},
            "confidence": 0.0
        }
    
    async def _generate_executive_summary(
        self, agenda_results: Dict, claim_results: Dict, counter_results: Dict, 
        evidence_results: Dict, meeting_metadata: Dict
    ) -> Dict[str, Any]:
        """경영진 요약 생성"""
        
        # 주요 통계 정리
        stats = {
            "agenda_count": len(agenda_results.get("agendas", [])),
            "claim_count": len(claim_results.get("claims", [])),
            "evidence_count": len(evidence_results.get("evidence_collection", [])),
            "counter_argument_count": len(counter_results.get("counter_arguments", [])),
            "high_priority_agendas": len([
                a for a in agenda_results.get("agendas", []) 
                if a.get("priority") == "high"
            ])
        }
        
        context = f"""
회의 메타데이터: {json.dumps(meeting_metadata, ensure_ascii=False, indent=2)[:500]}...
분석 통계: {json.dumps(stats, ensure_ascii=False)}
주요 아젠다: {len(agenda_results.get("agendas", []))}개
핵심 주장: {len(claim_results.get("claims", []))}개
"""
        
        question = """
다음 형식으로 경영진용 요약을 작성하세요:

{
    "key_outcomes": [
        "핵심 결과 1",
        "핵심 결과 2",
        "핵심 결과 3"
    ],
    "major_decisions": [
        {
            "decision": "주요 결정 사항",
            "rationale": "근거",
            "impact": "예상 영향"
        }
    ],
    "critical_issues": [
        {
            "issue": "중요 이슈",
            "urgency": "high|medium|low",
            "recommendation": "권고 사항"
        }
    ],
    "success_metrics": [
        "성공 지표 1",
        "성공 지표 2"
    ],
    "next_steps": [
        "다음 단계 1",
        "다음 단계 2"
    ],
    "executive_recommendation": "경영진을 위한 핵심 권고사항"
}

간결하고 실행 가능한 내용으로 작성하세요.
"""
        
        response = await self.think(context, question)
        
        try:
            if response.startswith("```json"):
                response = response.strip("```json").strip("```").strip()
            
            return json.loads(response)
            
        except json.JSONDecodeError:
            return {
                "key_outcomes": ["분석 완료"],
                "major_decisions": [],
                "critical_issues": [],
                "success_metrics": [],
                "next_steps": ["상세 검토 필요"],
                "executive_recommendation": "추가 분석이 필요합니다."
            }
    
    async def _create_detailed_analysis(
        self, agenda_results: Dict, claim_results: Dict, 
        counter_results: Dict, evidence_results: Dict
    ) -> Dict[str, Any]:
        """상세 분석 정리"""
        
        return {
            "agenda_analysis": {
                "total_agendas": len(agenda_results.get("agendas", [])),
                "priority_distribution": self._analyze_priority_distribution(agenda_results.get("agendas", [])),
                "category_breakdown": self._analyze_category_breakdown(agenda_results.get("agendas", [])),
                "completion_status": self._analyze_completion_status(agenda_results.get("agendas", []))
            },
            "argument_analysis": {
                "total_claims": len(claim_results.get("claims", [])),
                "logical_strength": claim_results.get("evidence_quality", {}).get("overall_score", 0.0),
                "fallacies_detected": len(claim_results.get("fallacies", [])),
                "consensus_level": self._calculate_consensus_level(claim_results, counter_results)
            },
            "evidence_analysis": {
                "evidence_count": len(evidence_results.get("evidence_collection", [])),
                "credibility_score": evidence_results.get("credibility_analysis", {}).get("overall_credibility", 0.0),
                "source_diversity": len(evidence_results.get("credibility_analysis", {}).get("source_distribution", {})),
                "knowledge_gaps": len(evidence_results.get("knowledge_gaps", []))
            },
            "counter_analysis": {
                "counter_arguments": len(counter_results.get("counter_arguments", [])),
                "alternative_scenarios": len(counter_results.get("alternative_scenarios", [])),
                "risk_level": counter_results.get("risk_analysis", {}).get("overall_risk_level", "unknown")
            }
        }
    
    def _analyze_priority_distribution(self, agendas: List[Dict]) -> Dict[str, int]:
        """우선순위 분포 분석"""
        distribution = {"high": 0, "medium": 0, "low": 0}
        for agenda in agendas:
            priority = agenda.get("priority", "medium")
            distribution[priority] = distribution.get(priority, 0) + 1
        return distribution
    
    def _analyze_category_breakdown(self, agendas: List[Dict]) -> Dict[str, int]:
        """카테고리별 분석"""
        breakdown = {}
        for agenda in agendas:
            category = agenda.get("category", "unknown")
            breakdown[category] = breakdown.get(category, 0) + 1
        return breakdown
    
    def _analyze_completion_status(self, agendas: List[Dict]) -> Dict[str, int]:
        """완료 상태 분석"""
        status = {"completed": 0, "in_progress": 0, "pending": 0}
        for agenda in agendas:
            # 액션 아이템이 있으면 진행 중, 결과가 있으면 완료로 간주
            if agenda.get("outcomes"):
                status["completed"] += 1
            elif agenda.get("action_items"):
                status["in_progress"] += 1
            else:
                status["pending"] += 1
        return status
    
    def _calculate_consensus_level(self, claim_results: Dict, counter_results: Dict) -> str:
        """합의 수준 계산"""
        claims = claim_results.get("claims", [])
        counter_args = counter_results.get("counter_arguments", [])
        
        if not claims:
            return "unknown"
        
        # 반박이 있는 주장의 비율
        contested_ratio = len(counter_args) / len(claims) if claims else 0
        
        if contested_ratio < 0.3:
            return "high"
        elif contested_ratio < 0.7:
            return "medium"
        else:
            return "low"
    
    async def _extract_action_items(
        self, agenda_results: Dict, claim_results: Dict, counter_results: Dict
    ) -> List[Dict]:
        """액션 아이템 추출"""
        
        action_items = []
        
        # 아젠다에서 액션 아이템 추출
        for agenda in agenda_results.get("agendas", []):
            for action in agenda.get("action_items", []):
                action_items.append({
                    "id": len(action_items) + 1,
                    "source": "agenda",
                    "source_id": agenda.get("id"),
                    "task": action.get("task", ""),
                    "assignee": action.get("assignee", "TBD"),
                    "deadline": action.get("deadline", "TBD"),
                    "priority": agenda.get("priority", "medium"),
                    "category": "agenda_follow_up",
                    "dependencies": [],
                    "success_criteria": []
                })
        
        # 반박 논리에서 추가 액션 아이템 도출
        for counter_arg in counter_results.get("counter_arguments", []):
            if counter_arg.get("supporting_questions"):
                action_items.append({
                    "id": len(action_items) + 1,
                    "source": "counter_argument",
                    "source_id": counter_arg.get("id"),
                    "task": f"반박 논거 검증: {counter_arg.get('supporting_questions', [''])[0]}",
                    "assignee": "TBD",
                    "deadline": "TBD",
                    "priority": "medium",
                    "category": "verification",
                    "dependencies": [],
                    "success_criteria": ["검증 완료", "결과 문서화"]
                })
        
        # 우선순위별 정렬
        priority_order = {"high": 1, "medium": 2, "low": 3}
        action_items.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 2))
        
        return action_items[:15]  # 최대 15개
    
    async def _generate_recommendations(
        self, claim_results: Dict, counter_results: Dict, evidence_results: Dict
    ) -> List[Dict]:
        """권고사항 생성"""
        
        recommendations = []
        
        # 증거 품질 기반 권고
        evidence_quality = evidence_results.get("credibility_analysis", {})
        if evidence_quality.get("overall_credibility", 0) < 0.6:
            recommendations.append({
                "id": len(recommendations) + 1,
                "type": "evidence_quality",
                "category": "data_collection",
                "title": "증거 수집 강화 필요",
                "description": "현재 증거의 신뢰도가 낮습니다. 추가적인 신뢰할 수 있는 출처에서 데이터를 수집하세요.",
                "priority": "high",
                "implementation_effort": "medium",
                "expected_impact": "high",
                "timeline": "2주 이내"
            })
        
        # 논리 오류 기반 권고
        fallacies = claim_results.get("fallacies", [])
        if len(fallacies) > 2:
            recommendations.append({
                "id": len(recommendations) + 1,
                "type": "logical_improvement",
                "category": "argumentation",
                "title": "논리 구조 개선 필요",
                "description": f"{len(fallacies)}개의 논리 오류가 발견되었습니다. 주장의 논리적 타당성을 재검토하세요.",
                "priority": "medium",
                "implementation_effort": "low",
                "expected_impact": "medium",
                "timeline": "1주 이내"
            })
        
        # 리스크 기반 권고
        risk_analysis = counter_results.get("risk_analysis", {})
        if risk_analysis.get("overall_risk_level") == "high":
            recommendations.append({
                "id": len(recommendations) + 1,
                "type": "risk_mitigation",
                "category": "risk_management",
                "title": "리스크 완화 계획 수립",
                "description": "높은 수준의 리스크가 식별되었습니다. 구체적인 완화 전략을 수립하세요.",
                "priority": "high",
                "implementation_effort": "high",
                "expected_impact": "high",
                "timeline": "3주 이내"
            })
        
        return recommendations
    
    async def _assess_overall_risks(
        self, counter_results: Dict, evidence_results: Dict, claim_results: Dict
    ) -> Dict[str, Any]:
        """전체 리스크 평가"""
        
        # 개별 리스크 수집
        counter_risks = counter_results.get("risk_analysis", {})
        evidence_gaps = evidence_results.get("knowledge_gaps", [])
        logical_fallacies = claim_results.get("fallacies", [])
        
        # 리스크 카테고리별 점수 계산
        risk_scores = {
            "operational": min(len(logical_fallacies) * 0.2, 1.0),
            "strategic": min(len(evidence_gaps) * 0.15, 1.0),
            "reputational": 0.3 if len(logical_fallacies) > 3 else 0.1,
            "financial": counter_risks.get("risk_categories", {}).get("financial", 0)
        }
        
        # 전체 리스크 레벨
        avg_risk_score = sum(risk_scores.values()) / len(risk_scores)
        overall_risk_level = "high" if avg_risk_score > 0.7 else "medium" if avg_risk_score > 0.4 else "low"
        
        return {
            "overall_risk_level": overall_risk_level,
            "risk_scores": risk_scores,
            "critical_risks": [
                "논리적 오류로 인한 신뢰도 하락" if len(logical_fallacies) > 2 else None,
                "증거 부족으로 인한 결정의 불확실성" if len(evidence_gaps) > 3 else None,
                "반박 논거에 대한 대응 부족" if len(counter_results.get("counter_arguments", [])) > 5 else None
            ],
            "mitigation_required": avg_risk_score > 0.6,
            "monitoring_needed": [
                "논리적 일관성",
                "증거의 신뢰도",
                "이해관계자 반응"
            ]
        }
    
    async def _plan_follow_up(
        self, action_items: List[Dict], recommendations: List[Dict], risk_assessment: Dict
    ) -> Dict[str, Any]:
        """후속 조치 계획"""
        
        # 단기/중기/장기 분류
        short_term = []  # 1-2주
        medium_term = []  # 1-2개월
        long_term = []   # 3개월 이상
        
        for item in action_items[:10]:  # 상위 10개만
            if "1주" in item.get("timeline", "") or item.get("priority") == "high":
                short_term.append(item.get("task", ""))
            elif "2주" in item.get("timeline", "") or "1개월" in item.get("timeline", ""):
                medium_term.append(item.get("task", ""))
            else:
                long_term.append(item.get("task", ""))
        
        # 권고사항도 포함
        for rec in recommendations:
            timeline = rec.get("timeline", "")
            if "1주" in timeline or rec.get("priority") == "high":
                short_term.append(rec.get("title", ""))
        
        return {
            "immediate_actions": short_term[:5],  # 최대 5개
            "short_term_goals": medium_term[:5],
            "long_term_objectives": long_term[:3],
            "review_schedule": {
                "next_review": "2주 후",
                "review_frequency": "월 1회",
                "success_metrics": [
                    "액션 아이템 완료율",
                    "리스크 완화 진도",
                    "이해관계자 만족도"
                ]
            },
            "escalation_criteria": [
                "고위험 사항 발생 시",
                "액션 아이템 지연 시",
                "추가 자원 필요 시"
            ]
        }
    
    def _create_report_metadata(self, meeting_metadata: Dict, confidence: float) -> Dict[str, Any]:
        """보고서 메타데이터 생성"""
        
        return {
            "report_version": "1.0",
            "generation_date": datetime.now().isoformat(),
            "analysis_confidence": confidence,
            "meeting_info": {
                "date": meeting_metadata.get("date"),
                "duration": meeting_metadata.get("duration"),
                "participants": meeting_metadata.get("speakers", []),
                "title": meeting_metadata.get("title", "회의 분석 보고서")
            },
            "analysis_scope": {
                "agenda_analysis": True,
                "claim_verification": True,
                "counter_argumentation": True,
                "evidence_collection": True,
                "risk_assessment": True
            },
            "quality_indicators": {
                "completeness": min(confidence + 0.1, 1.0),
                "accuracy": confidence,
                "usefulness": confidence * 0.9
            },
            "limitations": [
                "AI 기반 분석으로 인간 전문가 검토 권장",
                "제한된 컨텍스트 내에서의 분석",
                "실시간 상황 변화 미반영"
            ]
        }
    
    def _calculate_confidence(
        self, agenda_results: Dict, claim_results: Dict, 
        evidence_results: Dict, counter_results: Dict
    ) -> float:
        """전체 신뢰도 계산"""
        
        # 각 에이전트별 신뢰도
        agenda_confidence = agenda_results.get("confidence", 0.0)
        claim_confidence = claim_results.get("confidence", 0.0)
        evidence_confidence = evidence_results.get("confidence", 0.0)
        counter_confidence = counter_results.get("confidence", 0.0)
        
        confidences = [agenda_confidence, claim_confidence, evidence_confidence, counter_confidence]
        valid_confidences = [c for c in confidences if c > 0]
        
        if not valid_confidences:
            return 0.0
        
        # 가중 평균 (각 에이전트의 중요도 고려)
        weights = [0.25, 0.3, 0.25, 0.2]  # claim > agenda = evidence > counter
        weighted_confidence = sum(c * w for c, w in zip(confidences, weights))
        
        # 완성도 보정
        completeness_bonus = len(valid_confidences) / 4 * 0.1
        
        final_confidence = min(weighted_confidence + completeness_bonus, 1.0)
        return round(final_confidence, 2)
    
    async def generate_report(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        보고서 생성 (파이프라인 호환용 래퍼 메서드)
        
        Args:
            agent_results: 다른 에이전트들의 분석 결과들
            
        Returns:
            종합 보고서
        """
        # agent_results를 process 메서드에 맞는 형식으로 변환
        input_data = {
            "agenda_results": agent_results.get("agendas", {}),
            "claim_results": agent_results.get("claims", {}),
            "counter_results": agent_results.get("counter_arguments", {}),
            "evidence_results": agent_results.get("evidence", {}),
            "meeting_metadata": agent_results.get("metadata", {}),
            "original_transcript": agent_results.get("transcript", {}).get("full_text", ""),
            "timestamp": agent_results.get("timestamp")
        }
        
        return await self.process(input_data)