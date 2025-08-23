"""
멀티에이전트 오케스트레이터 (MultiAgentOrchestrator)

5개 에이전트 간의 협업을 조율하고 전체 분석 프로세스를 관리합니다.
- 워크플로우 관리
- 에이전트 간 데이터 전달
- 결과 통합
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .agenda_miner import AgendaMiner
from .claim_checker import ClaimChecker
from .counter_arguer import CounterArguer
from .evidence_hunter import EvidenceHunter
from .summarizer import Summarizer

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """멀티에이전트 협업 조율자"""
    
    def __init__(self, llm_client=None, retriever=None):
        self.llm_client = llm_client
        self.retriever = retriever
        
        # 에이전트 인스턴스 생성
        self.agenda_miner = AgendaMiner(llm_client)
        self.claim_checker = ClaimChecker(llm_client)
        self.counter_arguer = CounterArguer(llm_client)
        self.evidence_hunter = EvidenceHunter(llm_client, retriever)
        self.summarizer = Summarizer(llm_client)
        
        # 실행 상태 추적
        self.execution_state = "idle"  # idle, running, completed, error
        self.current_step = 0
        self.total_steps = 5
        self.step_progress = {}
        
        # 워크플로우 정의
        self.workflow = [
            {
                "step": 1,
                "name": "agenda_mining",
                "agent": self.agenda_miner,
                "description": "핵심 아젠다 추출",
                "dependencies": []
            },
            {
                "step": 2,
                "name": "claim_checking",
                "agent": self.claim_checker,
                "description": "주장-근거 구조 분석",
                "dependencies": ["agenda_mining"]
            },
            {
                "step": 3,
                "name": "evidence_hunting",
                "agent": self.evidence_hunter,
                "description": "증거 수집 및 검증",
                "dependencies": ["claim_checking"]
            },
            {
                "step": 4,
                "name": "counter_arguing",
                "agent": self.counter_arguer,
                "description": "반박 논리 및 대안 제시",
                "dependencies": ["claim_checking"]
            },
            {
                "step": 5,
                "name": "summarizing",
                "agent": self.summarizer,
                "description": "종합 분석 및 보고서 생성",
                "dependencies": ["agenda_mining", "claim_checking", "evidence_hunting", "counter_arguing"]
            }
        ]
    
    async def analyze_meeting(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        전체 회의 분석 실행
        
        Args:
            meeting_data: {
                "transcript": str,         # 회의록 전문
                "speakers": List[str],     # 발화자 목록
                "timeline": List[Dict],    # 타임라인 정보
                "metadata": Dict,          # 회의 메타데이터
                "analysis_options": Dict   # 분석 옵션
            }
            
        Returns:
            종합 분석 결과
        """
        logger.info("MultiAgentOrchestrator: 회의 분석 시작")
        
        try:
            self.execution_state = "running"
            self.current_step = 0
            self._reset_progress()
            
            # 입력 데이터 검증
            if not self._validate_input(meeting_data):
                return self._create_error_result("입력 데이터가 유효하지 않습니다.")
            
            # 분석 결과 저장소
            results = {
                "input_data": meeting_data,
                "step_results": {},
                "execution_log": []
            }
            
            # 워크플로우 실행
            await self._execute_workflow(meeting_data, results)
            
            # 최종 결과 정리
            final_result = await self._prepare_final_result(results)
            
            self.execution_state = "completed"
            logger.info("MultiAgentOrchestrator: 회의 분석 완료")
            
            return final_result
            
        except Exception as e:
            self.execution_state = "error"
            logger.error(f"MultiAgentOrchestrator 분석 오류: {str(e)}")
            return self._create_error_result(str(e))
    
    def _validate_input(self, meeting_data: Dict[str, Any]) -> bool:
        """입력 데이터 유효성 검증"""
        
        required_fields = ["transcript"]
        for field in required_fields:
            if not meeting_data.get(field):
                logger.error(f"필수 필드 누락: {field}")
                return False
        
        transcript = meeting_data.get("transcript", "")
        if len(transcript.strip()) < 50:  # 최소 50자
            logger.error("회의록이 너무 짧습니다.")
            return False
        
        return True
    
    def _reset_progress(self):
        """진행률 초기화"""
        self.step_progress = {}
        for step_info in self.workflow:
            step_name = step_info["name"]
            self.step_progress[step_name] = {
                "status": "pending",
                "progress": 0.0,
                "start_time": None,
                "end_time": None,
                "error": None
            }
    
    async def _execute_workflow(self, meeting_data: Dict[str, Any], results: Dict[str, Any]):
        """워크플로우 실행"""
        
        # 병렬 실행 가능한 단계 식별
        parallel_steps = self._identify_parallel_steps()
        
        for step_group in parallel_steps:
            # 각 그룹 내의 단계들을 병렬로 실행
            tasks = []
            for step_info in step_group:
                task = self._execute_step(step_info, meeting_data, results)
                tasks.append(task)
            
            # 병렬 실행 대기
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def _identify_parallel_steps(self) -> List[List[Dict]]:
        """병렬 실행 가능한 단계 그룹 식별"""
        
        # 의존성 기반으로 실행 순서 결정
        step_groups = [
            # 그룹 1: 의존성 없음
            [step for step in self.workflow if not step["dependencies"]],
            
            # 그룹 2: agenda_mining에 의존
            [step for step in self.workflow if step["dependencies"] == ["agenda_mining"]],
            
            # 그룹 3: claim_checking에 의존 (병렬 가능)
            [step for step in self.workflow if "claim_checking" in step["dependencies"] and len(step["dependencies"]) == 1],
            
            # 그룹 4: 모든 결과에 의존
            [step for step in self.workflow if len(step["dependencies"]) > 2]
        ]
        
        return [group for group in step_groups if group]  # 빈 그룹 제거
    
    async def _execute_step(self, step_info: Dict, meeting_data: Dict[str, Any], results: Dict[str, Any]):
        """개별 단계 실행"""
        
        step_name = step_info["name"]
        agent = step_info["agent"]
        
        try:
            # 단계 시작
            self.current_step += 1
            self.step_progress[step_name]["status"] = "running"
            self.step_progress[step_name]["start_time"] = datetime.now().isoformat()
            self.step_progress[step_name]["progress"] = 0.1
            
            logger.info(f"단계 실행 시작: {step_name}")
            
            # 의존성 확인 및 입력 데이터 준비
            step_input = await self._prepare_step_input(step_name, meeting_data, results)
            
            self.step_progress[step_name]["progress"] = 0.3
            
            # 에이전트 실행
            step_result = await agent.process(step_input)
            
            self.step_progress[step_name]["progress"] = 0.9
            
            # 결과 저장
            results["step_results"][step_name] = step_result
            results["execution_log"].append({
                "step": step_name,
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "agent": agent.name,
                "result_keys": list(step_result.keys())
            })
            
            # 단계 완료
            self.step_progress[step_name]["status"] = "completed"
            self.step_progress[step_name]["progress"] = 1.0
            self.step_progress[step_name]["end_time"] = datetime.now().isoformat()
            
            logger.info(f"단계 실행 완료: {step_name}")
            
        except Exception as e:
            # 오류 처리
            self.step_progress[step_name]["status"] = "error"
            self.step_progress[step_name]["error"] = str(e)
            
            results["execution_log"].append({
                "step": step_name,
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "agent": agent.name,
                "error": str(e)
            })
            
            logger.error(f"단계 실행 오류 ({step_name}): {str(e)}")
            # 오류가 발생해도 다른 단계는 계속 진행
    
    async def _prepare_step_input(self, step_name: str, meeting_data: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """단계별 입력 데이터 준비"""
        
        step_results = results.get("step_results", {})
        base_input = {
            "transcript": meeting_data.get("transcript", ""),
            "speakers": meeting_data.get("speakers", []),
            "timeline": meeting_data.get("timeline", []),
            "metadata": meeting_data.get("metadata", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        # 단계별 특화 입력 준비
        if step_name == "agenda_mining":
            return base_input
        
        elif step_name == "claim_checking":
            agenda_result = step_results.get("agenda_mining", {})
            base_input.update({
                "agendas": agenda_result.get("agendas", [])
            })
            return base_input
        
        elif step_name == "evidence_hunting":
            claim_result = step_results.get("claim_checking", {})
            base_input.update({
                "claims": claim_result.get("claims", []),
                "sources": meeting_data.get("analysis_options", {}).get("sources", ["all"])
            })
            return base_input
        
        elif step_name == "counter_arguing":
            claim_result = step_results.get("claim_checking", {})
            agenda_result = step_results.get("agenda_mining", {})
            base_input.update({
                "claims": claim_result.get("claims", []),
                "agendas": agenda_result.get("agendas", []),
                "logical_structure": claim_result.get("logical_structure", {})
            })
            return base_input
        
        elif step_name == "summarizing":
            return {
                "agenda_results": step_results.get("agenda_mining", {}),
                "claim_results": step_results.get("claim_checking", {}),
                "counter_results": step_results.get("counter_arguing", {}),
                "evidence_results": step_results.get("evidence_hunting", {}),
                "meeting_metadata": meeting_data.get("metadata", {}),
                "original_transcript": meeting_data.get("transcript", ""),
                "timestamp": datetime.now().isoformat()
            }
        
        return base_input
    
    async def _prepare_final_result(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """최종 결과 정리"""
        
        step_results = results.get("step_results", {})
        execution_log = results.get("execution_log", [])
        
        # 주요 결과 추출
        final_summary = step_results.get("summarizing", {})
        
        # 전체 분석 메타데이터
        analysis_metadata = {
            "analysis_id": f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "execution_time": self._calculate_execution_time(execution_log),
            "steps_completed": len([log for log in execution_log if log.get("status") == "completed"]),
            "steps_failed": len([log for log in execution_log if log.get("status") == "error"]),
            "overall_confidence": self._calculate_overall_confidence(step_results),
            "agents_used": [
                {"name": agent.name, "description": agent.description}
                for agent in [self.agenda_miner, self.claim_checker, self.counter_arguer, self.evidence_hunter, self.summarizer]
            ]
        }
        
        # 최종 결과 구성
        final_result = {
            "analysis_metadata": analysis_metadata,
            "executive_summary": final_summary.get("executive_summary", {}),
            "detailed_analysis": final_summary.get("detailed_analysis", {}),
            "action_items": final_summary.get("action_items", []),
            "recommendations": final_summary.get("recommendations", []),
            "risk_assessment": final_summary.get("risk_assessment", {}),
            "follow_up": final_summary.get("follow_up", {}),
            
            # 단계별 상세 결과 (선택적 포함)
            "detailed_results": {
                "agenda_analysis": step_results.get("agenda_mining", {}),
                "claim_analysis": step_results.get("claim_checking", {}),
                "counter_analysis": step_results.get("counter_arguing", {}),
                "evidence_analysis": step_results.get("evidence_hunting", {})
            },
            
            "execution_log": execution_log,
            "processing_time": analysis_metadata["execution_time"]
        }
        
        return final_result
    
    def _calculate_execution_time(self, execution_log: List[Dict]) -> Dict[str, Any]:
        """실행 시간 계산"""
        
        if not execution_log:
            return {"total_seconds": 0, "formatted": "0초"}
        
        # 시작 시간과 종료 시간 찾기
        timestamps = [log.get("timestamp") for log in execution_log if log.get("timestamp")]
        if len(timestamps) < 2:
            return {"total_seconds": 0, "formatted": "0초"}
        
        try:
            start_time = min(timestamps)
            end_time = max(timestamps)
            
            # 간단한 시간 차이 계산 (실제로는 더 정교한 파싱 필요)
            total_seconds = 30  # 임시 값
            
            return {
                "total_seconds": total_seconds,
                "formatted": f"{total_seconds}초",
                "start_time": start_time,
                "end_time": end_time
            }
            
        except Exception:
            return {"total_seconds": 0, "formatted": "계산 실패"}
    
    def _calculate_overall_confidence(self, step_results: Dict[str, Any]) -> float:
        """전체 신뢰도 계산"""
        
        confidences = []
        for step_result in step_results.values():
            confidence = step_result.get("confidence")
            if confidence is not None and 0 <= confidence <= 1:
                confidences.append(confidence)
        
        if not confidences:
            return 0.0
        
        return round(sum(confidences) / len(confidences), 2)
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """오류 결과 생성"""
        
        return {
            "error": True,
            "error_message": error_message,
            "analysis_metadata": {
                "analysis_id": f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "execution_time": {"total_seconds": 0, "formatted": "실패"},
                "steps_completed": 0,
                "steps_failed": 1,
                "overall_confidence": 0.0
            },
            "executive_summary": {},
            "detailed_analysis": {},
            "action_items": [],
            "recommendations": [],
            "risk_assessment": {},
            "follow_up": {},
            "detailed_results": {},
            "execution_log": [{
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": error_message
            }]
        }
    
    def get_progress(self) -> Dict[str, Any]:
        """현재 진행률 반환"""
        
        total_progress = sum(step.get("progress", 0) for step in self.step_progress.values())
        overall_progress = total_progress / len(self.step_progress) if self.step_progress else 0.0
        
        return {
            "execution_state": self.execution_state,
            "overall_progress": round(overall_progress, 2),
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "step_details": self.step_progress,
            "estimated_remaining": self._estimate_remaining_time()
        }
    
    def _estimate_remaining_time(self) -> str:
        """남은 시간 추정"""
        
        completed_steps = len([s for s in self.step_progress.values() if s.get("status") == "completed"])
        running_steps = len([s for s in self.step_progress.values() if s.get("status") == "running"])
        pending_steps = len([s for s in self.step_progress.values() if s.get("status") == "pending"])
        
        if pending_steps == 0 and running_steps == 0:
            return "완료"
        
        # 단계별 평균 소요 시간 추정 (실제로는 이전 실행 기록 기반)
        avg_step_time = 15  # 초
        estimated_seconds = (running_steps * 0.5 + pending_steps) * avg_step_time
        
        if estimated_seconds < 60:
            return f"약 {int(estimated_seconds)}초"
        else:
            return f"약 {int(estimated_seconds / 60)}분"
    
    async def stop_analysis(self) -> bool:
        """분석 중단"""
        
        if self.execution_state == "running":
            self.execution_state = "cancelled"
            logger.info("MultiAgentOrchestrator: 분석이 사용자에 의해 중단되었습니다.")
            return True
        
        return False