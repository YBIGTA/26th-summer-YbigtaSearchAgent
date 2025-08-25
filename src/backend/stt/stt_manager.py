"""
STT 엔진 매니저
Whisper와 ReturnZero를 통합 관리
"""

import os
from typing import Dict, Any, Optional
try:
    from .whisper_stt import transcribe_audio
except ImportError:
    transcribe_audio = None
    
try:
    from .returnzero_client import ReturnZeroSTTClient
except ImportError:
    ReturnZeroSTTClient = None

try:
    from ..nlp.transcript_postprocessor import TranscriptPostProcessor
except ImportError:
    TranscriptPostProcessor = None



class STTManager:
    def __init__(self):
        self.engines = ["whisper", "returnzero"]
        self.default_engine = "returnzero"
        self.postprocessor = TranscriptPostProcessor() if TranscriptPostProcessor else None
        
    def get_available_engines(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 STT 엔진 목록을 반환합니다."""
        engines = {}
        
        # Whisper 엔진 확인
        engines["whisper"] = {
            "name": "OpenAI Whisper",
            "available": transcribe_audio is not None,
            "languages": ["ko", "en", "ja", "zh", "es", "de", "fr", "auto"],
            "models": ["tiny", "base", "small", "medium", "large"],
            "features": ["multilingual", "timestamps", "local_processing"],
            "description": "OpenAI의 오픈소스 음성 인식 모델"
        }
        
        
        # ReturnZero 엔진 확인
        rtzr_available = bool(
            (os.getenv("RETURNZERO_USER_KEY") or os.getenv("RETURNZERO_CLIENT_ID")) and 
            (os.getenv("RETURNZERO_USER_SECRET") or os.getenv("RETURNZERO_CLIENT_SECRET"))
        )
        
        engines["returnzero"] = {
            "name": "ReturnZero VITO",
            "available": True,  # 임시로 True 설정
            "languages": ["ko", "en", "ja", "zh", "es", "de", "fr"],
            "features": ["korean_specialized", "diarization", "domain_models"],
            "domains": ["NEWS", "BUSINESS", "FINANCIAL", "GENERAL"],
            "description": "한국어 특화 음성 인식 서비스"
        }
        
        return engines
    
    def transcribe(self,
                  file_path: str,
                  engine: str = None,
                  language: str = "ko",
                  apply_postprocessing: bool = True,
                  **kwargs) -> Dict[str, Any]:
        """
        지정된 엔진으로 음성을 텍스트로 변환합니다.
        
        Args:
            file_path: 오디오 파일 경로
            engine: STT 엔진 ("whisper" or "returnzero")
            language: 언어 코드
            apply_postprocessing: 후처리 적용 여부
            **kwargs: 엔진별 추가 옵션
        
        Returns:
            통일된 형식의 전사 결과
        """
        engine = engine or self.default_engine
        
        if engine not in self.engines:
            raise ValueError(f"지원하지 않는 엔진입니다: {engine}")
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {file_path}")
        
        print(f"🎙️ {engine} 엔진으로 STT 처리 시작: {os.path.basename(file_path)}")
        
        try:
            # 기본 STT 처리
            if engine == "whisper":
                result = self._transcribe_with_whisper(file_path, language, **kwargs)
            elif engine == "returnzero":
                result = self._transcribe_with_returnzero(file_path, language, **kwargs)
            else:
                raise ValueError(f"알 수 없는 엔진: {engine}")
            
            # 후처리 적용
            if apply_postprocessing and self.postprocessor:
                print("🔧 전사 후처리 적용 중...")
                result = self.postprocessor.process(result)
                print("✅ 전사 후처리 완료")
            else:
                print("⚠️ 후처리 스킵됨")
            
            return result
                
        except Exception as e:
            print(f"❌ STT 처리 실패: {e}")
            raise
    
    def _transcribe_with_whisper(self, 
                               file_path: str, 
                               language: str = "ko",
                               model: str = "base",
                               **kwargs) -> Dict[str, Any]:
        """Whisper로 전사합니다."""
        if transcribe_audio is None:
            raise ImportError("Whisper 라이브러리가 설치되지 않았습니다. pip install openai-whisper를 실행하세요.")
        
        # 언어 변환 (auto -> None)
        whisper_language = None if language == "auto" else language
        
        result = transcribe_audio(
            file_path=file_path,
            model_name=model,
            language=whisper_language
        )
        
        # 화자 정보 추가 (Whisper는 화자 분리 미지원)
        segments = []
        for i, segment in enumerate(result.get("segments", [])):
            segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"],
                "speaker": "Speaker 1",  # 기본 화자
                "confidence": 1.0
            })
        
        return {
            "text": result["text"],
            "language": result.get("language", language),
            "segments": segments,
            "speakers": ["Speaker 1"],
            "engine": "whisper",
            "model": model,
            "duration": segments[-1]["end"] if segments else 0.0
        }
    
    def _transcribe_with_returnzero(self,
                                  file_path: str,
                                  language: str = "ko",
                                  use_diarization: bool = True,
                                  domain: str = None,
                                  **kwargs) -> Dict[str, Any]:
        """ReturnZero로 전사합니다."""
        client = ReturnZeroSTTClient()
        
        result = client.transcribe(
            audio_file_path=file_path,
            language=language,
            use_diarization=use_diarization,
            use_domain_lm=bool(domain),
            domain=domain
        )
        
        # 결과에 엔진 정보 추가
        result["engine"] = "returnzero"
        if domain:
            result["domain"] = domain
        
        return result
    
    def validate_engine_config(self, engine: str) -> Dict[str, Any]:
        """엔진 설정이 유효한지 확인합니다."""
        result = {
            "engine": engine,
            "available": False,
            "error": None
        }
        
        try:
            if engine == "whisper":
                # Whisper는 라이브러리가 있을 때만 사용 가능
                result["available"] = transcribe_audio is not None
                if not result["available"]:
                    result["error"] = "Whisper 라이브러리가 설치되지 않았습니다."
                
            elif engine == "returnzero":
                client_id = os.getenv("RETURNZERO_USER_KEY") or os.getenv("RETURNZERO_CLIENT_ID")
                client_secret = os.getenv("RETURNZERO_USER_SECRET") or os.getenv("RETURNZERO_CLIENT_SECRET")
                
                if not client_id or not client_secret:
                    result["error"] = "ReturnZero API 키가 설정되지 않았습니다."
                else:
                    # 일단 API 키가 있으면 available로 처리
                    result["available"] = True
                    # TODO: 실제 API 연결 테스트는 필요시에만
                    # try:
                    #     client = ReturnZeroSTTClient(client_id, client_secret)
                    #     if not client.validate_credentials():
                    #         result["available"] = False
                    #         result["error"] = "ReturnZero API 키가 유효하지 않습니다."
                    # except Exception as e:
                    #     result["available"] = False
                    #     result["error"] = f"ReturnZero API 연결 오류: {str(e)}"
            else:
                result["error"] = f"알 수 없는 엔진: {engine}"
                
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def get_engine_info(self, engine: str) -> Optional[Dict[str, Any]]:
        """특정 엔진의 정보를 반환합니다."""
        engines = self.get_available_engines()
        return engines.get(engine)
    
    def set_default_engine(self, engine: str):
        """기본 STT 엔진을 설정합니다."""
        if engine in self.engines:
            self.default_engine = engine
        else:
            raise ValueError(f"지원하지 않는 엔진입니다: {engine}")


# 싱글톤 인스턴스
stt_manager = STTManager()