"""
Upstage LLM 클라이언트 설정
"""

import os
import logging
from typing import Optional, List
from langchain_upstage import ChatUpstage
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class UpstageClient:
    """Upstage LLM 클라이언트 래퍼"""
    
    def __init__(self, api_key: str = None, model: str = "solar-pro2"):
        """
        Upstage 클라이언트 초기화
        
        Args:
            api_key: Upstage API 키 (None이면 환경변수에서 로드)
            model: 사용할 모델 이름
        """
        self.api_key = api_key or self._get_api_key()
        self.model = model
        
        if not self.api_key:
            raise ValueError("Upstage API 키가 설정되지 않았습니다.")
        
        try:
            self.client = ChatUpstage(
                api_key=self.api_key,
                model=self.model,
                temperature=0.7,
                max_tokens=2000
            )
            logger.info(f"✅ Upstage 클라이언트 초기화 완료 (모델: {self.model})")
        except Exception as e:
            logger.error(f"❌ Upstage 클라이언트 초기화 실패: {e}")
            raise
    
    def _get_api_key(self) -> Optional[str]:
        """환경변수에서 API 키 로드 (순차적으로 시도)"""
        api_key_vars = [
            "UPSTAGE_API_KEY",
            "UPSTAGE_API_KEY1", 
            "UPSTAGE_API_KEY2",
            "UPSTAGE_API_KEY3",
            "UPSTAGE_API_KEY4",
            "UPSTAGE_API_KEY5",
            "UPSTAGE_API_KEY6",
            "UPSTAGE_API_KEY7",
            "UPSTAGE_API_KEY8"
        ]
        
        for var_name in api_key_vars:
            api_key = os.getenv(var_name)
            if api_key and api_key.strip() and api_key != "your_upstage_api_key_here":
                logger.info(f"✅ API 키 로드: {var_name}")
                return api_key.strip()
        
        logger.warning("⚠️ Upstage API 키를 찾을 수 없습니다.")
        return None
    
    async def invoke_async(self, messages: List[dict]) -> str:
        """비동기 LLM 호출"""
        try:
            # dict를 langchain message 객체로 변환
            langchain_messages = []
            for msg in messages:
                if msg.get("role") == "system":
                    langchain_messages.append(SystemMessage(content=msg["content"]))
                elif msg.get("role") == "user" or msg.get("role") == "human":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
            
            response = await self.client.ainvoke(langchain_messages)
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Upstage LLM 호출 실패: {e}")
            raise
    
    def invoke_sync(self, messages: List[dict]) -> str:
        """동기 LLM 호출"""
        try:
            # dict를 langchain message 객체로 변환
            langchain_messages = []
            for msg in messages:
                if msg.get("role") == "system":
                    langchain_messages.append(SystemMessage(content=msg["content"]))
                elif msg.get("role") == "user" or msg.get("role") == "human":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
            
            response = self.client.invoke(langchain_messages)
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Upstage LLM 호출 실패: {e}")
            raise
    
    def validate_connection(self) -> bool:
        """API 연결 테스트"""
        try:
            test_messages = [
                {"role": "user", "content": "Hello, this is a connection test."}
            ]
            response = self.invoke_sync(test_messages)
            logger.info("✅ Upstage API 연결 테스트 성공")
            return True
        except Exception as e:
            logger.error(f"❌ Upstage API 연결 테스트 실패: {e}")
            return False


def create_upstage_client() -> Optional[UpstageClient]:
    """
    Upstage 클라이언트 생성 함수
    
    Returns:
        UpstageClient 인스턴스 또는 None (실패시)
    """
    try:
        client = UpstageClient()
        if client.validate_connection():
            return client
        else:
            logger.warning("⚠️ Upstage 연결 검증 실패")
            return None
    except Exception as e:
        logger.error(f"❌ Upstage 클라이언트 생성 실패: {e}")
        return None