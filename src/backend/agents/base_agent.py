"""
기본 에이전트 클래스

모든 에이전트가 상속받는 베이스 클래스입니다.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """모든 에이전트의 기본 클래스"""
    
    def __init__(self, name: str, description: str, llm_client=None):
        self.name = name
        self.description = description
        self.llm_client = llm_client
        self.conversation_history: List[Dict[str, Any]] = []
        self.agent_state = "idle"  # idle, thinking, responding, error
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        에이전트의 핵심 처리 로직
        
        Args:
            input_data: 입력 데이터
            
        Returns:
            처리 결과
        """
        pass
    
    async def think(self, context: str, question: str) -> str:
        """
        LLM을 사용한 추론
        
        Args:
            context: 컨텍스트 정보
            question: 질문 또는 요청
            
        Returns:
            LLM의 응답
        """
        if not self.llm_client:
            logger.warning(f"{self.name}: LLM 클라이언트가 설정되지 않았습니다.")
            return "LLM 클라이언트가 설정되지 않았습니다."
            
        self.agent_state = "thinking"
        
        try:
            # 시스템 프롬프트 구성
            system_prompt = f"""
당신은 {self.name} 에이전트입니다.
역할: {self.description}

다음 지침을 따르세요:
1. 주어진 역할에 충실하게 분석하세요
2. 구체적이고 실행 가능한 결과를 제공하세요
3. 근거를 명확히 제시하세요
4. JSON 형태로 구조화된 응답을 하세요
"""
            
            user_prompt = f"""
컨텍스트:
{context}

요청:
{question}
"""
            
            # LLM 호출 (실제 구현에서는 각 LLM 클라이언트에 맞게 조정)
            response = await self._call_llm(system_prompt, user_prompt)
            
            # 대화 기록 저장
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "context": context,
                "question": question,
                "response": response
            })
            
            self.agent_state = "idle"
            return response
            
        except Exception as e:
            self.agent_state = "error"
            logger.error(f"{self.name} 에이전트 오류: {str(e)}")
            return f"에이전트 처리 중 오류 발생: {str(e)}"
    
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        LLM 호출 (서브클래스에서 구체적으로 구현)
        
        현재는 더미 구현, 실제로는 OpenAI/Upstage API 호출
        """
        if self.llm_client:
            # TODO: 실제 LLM 클라이언트 연동
            await asyncio.sleep(1)  # 시뮬레이션
            return f"{self.name}의 분석 결과 (더미)"
        else:
            return f"{self.name}: LLM 클라이언트 미설정"
    
    def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 반환"""
        return {
            "name": self.name,
            "description": self.description,
            "state": self.agent_state,
            "conversation_count": len(self.conversation_history),
            "last_activity": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }
    
    def reset(self):
        """에이전트 상태 초기화"""
        self.conversation_history.clear()
        self.agent_state = "idle"
        logger.info(f"{self.name} 에이전트가 초기화되었습니다.")