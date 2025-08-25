"""
반박 논리자 (CounterArguer)

제시된 주장들에 대한 반박 논리와 대안 시나리오를 제시합니다.
- 반대 논거 탐색
- 대안 관점 제시
- 비판적 분석
"""

import json
import logging
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CounterArguer(BaseAgent):
    """반대 논거 및 대안 시나리오 제시 전문 에이전트"""
    
    def __init__(self, llm_client=None):
        super().__init__(
            name="CounterArguer",
            description="반대 논거와 대안 시나리오를 제시하여 비판적 사고를 돕는 전문가",
            llm_client=llm_client
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        반박 논리 및 대안 분석
        
        Args:
            input_data: {
                "claims": List[Dict],          # ClaimChecker 결과
                "agendas": List[Dict],         # AgendaMiner 결과
                "logical_structure": Dict,     # 논리 구조
                "transcript": str,             # 원본 회의록
                "context": Dict               # 추가 컨텍스트
            }
            
        Returns:
            {
                "counter_arguments": List[Dict],    # 반박 논거
                "alternative_scenarios": List[Dict], # 대안 시나리오
                "devil_advocate": List[Dict],       # 악마의 변호사 관점
                "risk_analysis": Dict,              # 리스크 분석
                "confidence": float                 # 신뢰도
            }
        """
        logger.info("CounterArguer: 반박 논리 분석 시작")
        
        try:
            claims = input_data.get("claims", [])
            agendas = input_data.get("agendas", [])
            logical_structure = input_data.get("logical_structure", {})
            transcript = input_data.get("transcript", "")
            
            if not claims:
                return self._empty_result("분석할 주장이 제공되지 않았습니다.")
            
            # 1. 반박 논거 생성
            counter_arguments = await self._generate_counter_arguments(claims, transcript)
            
            # 2. 대안 시나리오 제시
            alternative_scenarios = await self._propose_alternatives(agendas, claims, logical_structure)
            
            # 3. 악마의 변호사 관점
            devil_advocate = await self._devils_advocate_analysis(claims, agendas)
            
            # 4. 리스크 분석
            risk_analysis = await self._analyze_risks(claims, alternative_scenarios)
            
            # 5. 신뢰도 계산
            confidence = self._calculate_confidence(counter_arguments, alternative_scenarios, claims)
            
            result = {
                "counter_arguments": counter_arguments,
                "alternative_scenarios": alternative_scenarios,
                "devil_advocate": devil_advocate,
                "risk_analysis": risk_analysis,
                "confidence": confidence,
                "agent": self.name,
                "timestamp": input_data.get("timestamp")
            }
            
            logger.info(f"CounterArguer: {len(counter_arguments)}개 반박 논거 생성 완료")
            return result
            
        except Exception as e:
            logger.error(f"CounterArguer 처리 오류: {str(e)}")
            return self._empty_result(str(e))
    
    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """빈 결과 반환"""
        return {
            "error": error_msg,
            "counter_arguments": [],
            "alternative_scenarios": [],
            "devil_advocate": [],
            "risk_analysis": {},
            "confidence": 0.0
        }
    
    async def _generate_counter_arguments(self, claims: List[Dict], transcript: str) -> List[Dict]:
        """반박 논거 생성"""
        
        claims_str = json.dumps(claims[:5], ensure_ascii=False, indent=2)
        
        context = f"""
분석된 주장들:
{claims_str}

원본 회의록 (샘플):
{transcript[:1500]}...
"""
        
        question = """
제시된 각 주장에 대해 가능한 반박 논거를 생성하세요:

{
    "counter_arguments": [
        {
            "id": 1,
            "target_claim_id": 2,
            "counter_claim": "반박 주장",
            "reasoning": "반박 근거",
            "evidence_type": "data|logic|precedent|expert_opinion|alternative_interpretation",
            "strength": "strong|moderate|weak",
            "potential_rebuttals": ["예상되는 재반박1", "예상되는 재반박2"],
            "supporting_questions": ["확인이 필요한 질문1", "확인이 필요한 질문2"],
            "implications": ["반박이 맞다면 생기는 결과1", "결과2"],
            "constructive_intent": true
        }
    ]
}

반박 논거 생성 원칙:
1. 건설적 비판을 목표로 함
2. 논리적 근거에 기반
3. 다각도에서 검토
4. 대안적 해석 제시
5. 잠재적 위험 요소 지적
"""
        
        response = await self.think(context, question)
        
        try:
            if response.startswith("```json"):
                response = response.strip("```json").strip("```").strip()
            
            result = json.loads(response)
            return result.get("counter_arguments", [])
            
        except json.JSONDecodeError:
            logger.warning("CounterArguer: 반박 논거 JSON 파싱 실패")
            return []
    
    async def _propose_alternatives(self, agendas: List[Dict], claims: List[Dict], logical_structure: Dict) -> List[Dict]:
        """대안 시나리오 제시"""
        
        agendas_str = json.dumps(agendas[:3], ensure_ascii=False, indent=2)
        
        context = f"""
회의 아젠다:
{agendas_str}

주요 주장들: {len(claims)}개
논리 구조: {json.dumps(logical_structure, ensure_ascii=False)[:500]}...
"""
        
        question = """
현재 논의된 방향 대신 고려할 수 있는 대안적 시나리오들을 제시하세요:

{
    "alternative_scenarios": [
        {
            "id": 1,
            "title": "대안 시나리오 제목",
            "description": "시나리오 상세 설명",
            "approach": "completely_different|modified_approach|phased_implementation|hybrid_solution",
            "advantages": ["장점1", "장점2", "장점3"],
            "disadvantages": ["단점1", "단점2"],
            "feasibility": "high|medium|low",
            "resource_requirements": {
                "time": "시간 소요",
                "budget": "예산 추정",
                "personnel": "인력 요구사항"
            },
            "key_assumptions": ["핵심 가정1", "핵심 가정2"],
            "success_metrics": ["성공 지표1", "성공 지표2"],
            "implementation_steps": ["단계1", "단계2", "단계3"]
        }
    ]
}

대안 유형:
- completely_different: 완전히 다른 접근
- modified_approach: 수정된 접근법
- phased_implementation: 단계별 실행
- hybrid_solution: 혼합 솔루션
"""
        
        response = await self.think(context, question)
        
        try:
            if response.startswith("```json"):
                response = response.strip("```json").strip("```").strip()
            
            result = json.loads(response)
            return result.get("alternative_scenarios", [])
            
        except json.JSONDecodeError:
            return []
    
    async def _devils_advocate_analysis(self, claims: List[Dict], agendas: List[Dict]) -> List[Dict]:
        """악마의 변호사 관점 분석"""
        
        context = f"""
주장 수: {len(claims)}개
아젠다 수: {len(agendas)}개
"""
        
        question = """
"악마의 변호사" 역할을 해서 다음 질문들을 제기하세요:

{
    "devil_advocate": [
        {
            "id": 1,
            "question": "도전적 질문",
            "concern": "우려사항",
            "worst_case_scenario": "최악의 시나리오",
            "hidden_assumptions": ["숨겨진 가정1", "숨겨진 가정2"],
            "overlooked_stakeholders": ["간과된 이해관계자1", "이해관계자2"],
            "unintended_consequences": ["의도치 않은 결과1", "결과2"],
            "stress_test_questions": ["스트레스 테스트 질문1", "질문2"],
            "category": "feasibility|ethics|resources|timing|politics|technical"
        }
    ]
}

악마의 변호사 역할:
1. 가장 비관적인 관점에서 검토
2. 숨겨진 리스크 발굴
3. 간과된 이해관계자 고려
4. 최악의 시나리오 상정
5. 근본적인 가정에 도전
"""
        
        response = await self.think(context, question)
        
        try:
            if response.startswith("```json"):
                response = response.strip("```json").strip("```").strip()
            
            result = json.loads(response)
            return result.get("devil_advocate", [])
            
        except json.JSONDecodeError:
            return []
    
    async def _analyze_risks(self, claims: List[Dict], alternative_scenarios: List[Dict]) -> Dict[str, Any]:
        """리스크 분석"""
        
        # 주장 기반 리스크 식별
        claim_risks = []
        for claim in claims[:5]:  # 최대 5개만
            if claim.get("confidence_level") == "low":
                claim_risks.append("불확실한 주장에 기반한 결정 리스크")
            if not claim.get("evidence"):
                claim_risks.append("근거 부족한 주장에 따른 리스크")
        
        # 대안 시나리오 기반 리스크
        scenario_risks = []
        for scenario in alternative_scenarios:
            if scenario.get("feasibility") == "low":
                scenario_risks.append(f"{scenario.get('title', '시나리오')}: 실현 가능성 낮음")
        
        # 전체 리스크 매트릭스
        risk_categories = {
            "operational": len([r for r in claim_risks if "결정" in r]),
            "strategic": len([r for r in scenario_risks if "시나리오" in r]),
            "reputational": 0,  # 추후 확장
            "financial": 0      # 추후 확장
        }
        
        # 전체 리스크 레벨
        total_risks = len(claim_risks) + len(scenario_risks)
        risk_level = "high" if total_risks > 5 else "medium" if total_risks > 2 else "low"
        
        return {
            "overall_risk_level": risk_level,
            "claim_based_risks": claim_risks,
            "scenario_risks": scenario_risks,
            "risk_categories": risk_categories,
            "total_risk_count": total_risks,
            "mitigation_needed": total_risks > 3,
            "recommendations": [
                "추가적인 근거 수집이 필요합니다" if len([c for c in claims if not c.get("evidence")]) > 2 else None,
                "대안 시나리오에 대한 심도 있는 검토가 필요합니다" if len(alternative_scenarios) > 3 else None,
                "리스크 완화 계획 수립이 권장됩니다" if total_risks > 5 else None
            ]
        }
    
    def _calculate_confidence(self, counter_arguments: List[Dict], alternative_scenarios: List[Dict], claims: List[Dict]) -> float:
        """신뢰도 계산"""
        
        if not claims:
            return 0.0
        
        # 기본 신뢰도
        confidence = 0.5
        
        # 반박 논거 품질
        strong_counters = len([c for c in counter_arguments if c.get("strength") == "strong"])
        if strong_counters > 0:
            confidence += 0.2
        
        # 대안 시나리오 다양성
        if len(alternative_scenarios) >= 2:
            confidence += 0.15
        
        # 건설적 의도
        constructive_counters = len([c for c in counter_arguments if c.get("constructive_intent")])
        if constructive_counters > 0:
            confidence += constructive_counters / len(counter_arguments) * 0.15
        
        # 원본 주장들의 품질에 반비례
        weak_claims = len([c for c in claims if c.get("confidence_level") == "low"])
        if weak_claims > 0:
            confidence += weak_claims / len(claims) * 0.1
            
        return min(confidence, 1.0)