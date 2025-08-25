"""
Dummy STT Client for Docker environment
Lightweight placeholder when heavy ML packages are not available
"""

from typing import Dict, Any, List
import time
import random


class DummySTTClient:
    """더미 STT 클라이언트 - 실제 ML 라이브러리 없이도 테스트 가능"""
    
    def __init__(self):
        self.name = "Dummy STT"
        self.available = True
    
    def transcribe(self, audio_path: str, language: str = "ko") -> Dict[str, Any]:
        """가짜 음성 인식 결과를 생성합니다."""
        # 실제 파일 존재 여부만 확인
        import os
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # 더미 데이터 생성
        duration = random.uniform(60, 300)  # 1-5분 랜덤
        
        # 가짜 발화 데이터
        dummy_utterances = [
            {
                "start_time": 0.0,
                "end_time": 8.5,
                "text": "안녕하세요, 오늘 회의를 시작하겠습니다.",
                "speaker": "Speaker_0",
                "confidence": 0.95
            },
            {
                "start_time": 9.0,
                "end_time": 18.2,
                "text": "네, 프로젝트 진행 상황을 공유드리겠습니다.",
                "speaker": "Speaker_1", 
                "confidence": 0.92
            },
            {
                "start_time": 19.5,
                "end_time": 32.1,
                "text": "현재 개발이 80% 정도 완료되었습니다.",
                "speaker": "Speaker_1",
                "confidence": 0.88
            }
        ]
        
        return {
            "status": "completed",
            "language": language,
            "duration": duration,
            "utterances": dummy_utterances,
            "speakers": ["Speaker_0", "Speaker_1"],
            "confidence": 0.92,
            "engine": "dummy",
            "note": "This is dummy data for testing without heavy ML dependencies"
        }
    
    def get_supported_languages(self) -> List[str]:
        """지원하는 언어 목록"""
        return ["ko", "en", "ja", "zh"]
    
    def is_available(self) -> bool:
        """STT 엔진 사용 가능 여부"""
        return True