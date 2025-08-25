"""
기본 에이전트 클래스

모든 에이전트가 상속받는 베이스 클래스입니다.
"""

import asyncio
import json
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
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
        LLM 호출 (Upstage API 사용)
        """
        if not self.llm_client:
            logger.error(f"{self.name}: LLM 클라이언트가 설정되지 않았습니다.")
            return f"{self.name}: LLM 클라이언트 미설정"
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Upstage 클라이언트의 invoke_async 메서드 사용
            response = await self.llm_client.invoke_async(messages)
            return response
            
        except Exception as e:
            logger.error(f"{self.name}: LLM 호출 실패: {e}")
            return f"{self.name}: LLM 호출 실패 - {str(e)}"
    
    def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 반환"""
        return {
            "name": self.name,
            "description": self.description,
            "state": self.agent_state,
            "conversation_count": len(self.conversation_history),
            "last_activity": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }
    
    async def analyze(self, input_data: Any) -> Dict[str, Any]:
        """
        에이전트 분석 수행 (process 메서드의 래퍼)
        
        Args:
            input_data: 분석할 데이터 (문자열이나 딕셔너리)
            
        Returns:
            분석 결과
        """
        # 입력 데이터를 딕셔너리 형태로 변환
        if isinstance(input_data, str):
            processed_input = {
                "transcript": input_data,  # AgendaMiner가 기대하는 키 사용
                "speakers": [],
                "timeline": [],
                "metadata": {},
                "timestamp": datetime.now().isoformat()
            }
        elif isinstance(input_data, dict):
            # 이미 딕셔너리인 경우 필요한 키들이 있는지 확인하고 없으면 추가
            processed_input = input_data.copy()
            if "transcript" not in processed_input and "content" in processed_input:
                processed_input["transcript"] = processed_input["content"]
            if "speakers" not in processed_input:
                processed_input["speakers"] = []
            if "timeline" not in processed_input:
                processed_input["timeline"] = []
            if "metadata" not in processed_input:
                processed_input["metadata"] = {}
        else:
            processed_input = {
                "transcript": str(input_data),
                "speakers": [],
                "timeline": [],
                "metadata": {},
                "timestamp": datetime.now().isoformat()
            }
        
        return await self.process(processed_input)
    
    def reset(self):
        """에이전트 상태 초기화"""
        self.conversation_history.clear()
        self.agent_state = "idle"
        logger.info(f"{self.name} 에이전트가 초기화되었습니다.")
    
    def parse_json_response(self, response: str, fallback_result: Any = None) -> Union[Dict, List, Any]:
        """
        LLM 응답에서 JSON을 안전하게 파싱
        
        Args:
            response: LLM 응답 문자열
            fallback_result: 파싱 실패 시 반환할 기본값
            
        Returns:
            파싱된 JSON 객체 또는 fallback_result
        """
        if not response or not response.strip():
            logger.warning(f"{self.name}: 빈 응답 수신")
            return fallback_result
        
        # 1. 코드 블록 제거
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]  # ```json 제거
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]  # ``` 제거
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]  # 마지막 ``` 제거
        
        cleaned_response = cleaned_response.strip()
        
        # 2. JSON 블록 추출 시도
        json_patterns = [
            # 완전한 JSON 객체/배열
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
            r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]',
            # 중첩된 JSON
            r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',
            r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, cleaned_response, re.DOTALL)
            if matches:
                for match in matches:
                    try:
                        result = json.loads(match)
                        logger.debug(f"{self.name}: JSON 파싱 성공")
                        return result
                    except json.JSONDecodeError:
                        continue
        
        # 3. 직접 JSON 파싱 시도
        try:
            result = json.loads(cleaned_response)
            logger.debug(f"{self.name}: 직접 JSON 파싱 성공")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"{self.name}: JSON 파싱 실패 - {str(e)}")
            logger.debug(f"{self.name}: 실패한 응답: {cleaned_response[:200]}...")
        
        # 4. 부분 복구 시도 (간단한 키-값 쌍)
        try:
            # 간단한 키-값 패턴 찾기
            simple_json = self._extract_simple_json(cleaned_response)
            if simple_json:
                logger.info(f"{self.name}: 부분 JSON 복구 성공")
                return simple_json
        except Exception as e:
            logger.debug(f"{self.name}: 부분 복구 실패 - {str(e)}")
        
        # 5. fallback 반환
        logger.warning(f"{self.name}: JSON 파싱 완전 실패, fallback 사용")
        return fallback_result if fallback_result is not None else {}
    
    def _extract_simple_json(self, text: str) -> Optional[Dict]:
        """간단한 JSON 구조 추출 시도"""
        try:
            # "key": "value" 패턴들을 찾아서 딕셔너리 구성
            key_value_pattern = r'"([^"]+)":\s*"([^"]*)"'
            matches = re.findall(key_value_pattern, text)
            
            if matches and len(matches) >= 2:  # 최소 2개 키-값 쌍
                result = {key: value for key, value in matches}
                return result
        except Exception:
            pass
        
        return None
    
    async def think_structured(self, context: str, question: str, expected_format: Dict[str, Any]) -> Dict[str, Any]:
        """
        구조화된 JSON 응답을 위한 개선된 think 메서드
        
        Args:
            context: 컨텍스트 정보
            question: 질문 또는 요청
            expected_format: 기대하는 JSON 형태의 예시
            
        Returns:
            구조화된 응답
        """
        if not self.llm_client:
            logger.warning(f"{self.name}: LLM 클라이언트가 설정되지 않았습니다.")
            return expected_format
            
        self.agent_state = "thinking"
        
        try:
            # 구조화된 시스템 프롬프트
            system_prompt = f"""
당신은 {self.name} 에이전트입니다.
역할: {self.description}

중요한 지침:
1. 반드시 유효한 JSON 형식으로만 응답하세요
2. JSON 앞뒤에 다른 텍스트를 추가하지 마세요
3. 아래 예시 형태를 정확히 따라하세요
4. 모든 문자열은 따옴표로 감싸세요
5. 중괄호와 대괄호를 정확히 맞추세요

응답 형식 예시:
{json.dumps(expected_format, ensure_ascii=False, indent=2)}
"""
            
            user_prompt = f"""
컨텍스트:
{context}

요청:
{question}

위 정보를 분석하여 지정된 JSON 형식으로 응답하세요. 오직 JSON만 출력하세요.
"""
            
            # LLM 호출
            response = await self._call_llm(system_prompt, user_prompt)
            
            # JSON 파싱
            result = self.parse_json_response(response, expected_format)
            
            # 대화 기록 저장
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "context": context,
                "question": question,
                "response": response,
                "parsed_result": result
            })
            
            self.agent_state = "idle"
            return result
            
        except Exception as e:
            self.agent_state = "error"
            logger.error(f"{self.name} 구조화된 추론 오류: {str(e)}")
            return expected_format