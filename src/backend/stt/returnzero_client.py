"""
ReturnZero STT API 클라이언트
JWT 토큰 자동 갱신 및 한국어 STT 특화
"""

import os
import json
import requests
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class ReturnZeroSTTClient:
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or os.getenv("RETURNZERO_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("RETURNZERO_CLIENT_SECRET")
        self.base_url = "https://openapi.vito.ai/v1"
        
        if not self.client_id or not self.client_secret:
            raise ValueError("ReturnZero client_id 및 client_secret가 필요합니다.")
        
        self.jwt_token = None
        self.token_expires_at = None
        
    def _authenticate(self) -> str:
        """JWT 토큰을 발급받습니다."""
        try:
            response = requests.post(
                f"{self.base_url}/authenticate",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )
            response.raise_for_status()
            
            data = response.json()
            self.jwt_token = data["access_token"]
            
            # 토큰 만료 시간 설정 (보통 24시간, 안전하게 23시간으로 설정)
            self.token_expires_at = datetime.now() + timedelta(hours=23)
            
            print(f"✅ ReturnZero JWT 토큰 발급 완료")
            return self.jwt_token
            
        except requests.RequestException as e:
            raise Exception(f"ReturnZero 인증 실패: {e}")
    
    def _get_valid_token(self) -> str:
        """유효한 JWT 토큰을 반환합니다. 필요시 자동 갱신."""
        if (not self.jwt_token or 
            not self.token_expires_at or 
            datetime.now() >= self.token_expires_at):
            return self._authenticate()
        
        return self.jwt_token
    
    def transcribe(self, 
                  audio_file_path: str,
                  language: str = "ko",
                  use_diarization: bool = True,
                  use_domain_lm: bool = False,
                  domain: str = None) -> Dict[str, Any]:
        """
        오디오 파일을 전사합니다.
        
        Args:
            audio_file_path: 오디오 파일 경로
            language: 언어 코드 (ko, en, ja, zh, es, de, fr)
            use_diarization: 화자 분리 사용 여부
            use_domain_lm: 도메인 특화 언어 모델 사용 여부
            domain: 도메인 (NEWS, BUSINESS, FINANCIAL, GENERAL)
        
        Returns:
            전사 결과 딕셔너리
        """
        token = self._get_valid_token()
        
        # 설정 구성
        config = {
            "use_multi_channel": False,
            "use_itn": True,  # Inverse Text Normalization
            "use_diarization": use_diarization,
            "use_paragraph_splitter": True,
            "paragraph_splitter": {
                "max": 50
            }
        }
        
        if language != "ko":
            config["language"] = language
        
        if use_domain_lm and domain:
            config["domain_lm"] = domain
        
        try:
            with open(audio_file_path, "rb") as audio_file:
                response = requests.post(
                    f"{self.base_url}/transcribe",
                    headers={"Authorization": f"Bearer {token}"},
                    data={"config": json.dumps(config)},
                    files={"file": audio_file}
                )
                response.raise_for_status()
                
            result = response.json()
            return self._parse_response(result)
            
        except requests.RequestException as e:
            raise Exception(f"ReturnZero STT 요청 실패: {e}")
        except FileNotFoundError:
            raise Exception(f"오디오 파일을 찾을 수 없습니다: {audio_file_path}")
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """ReturnZero API 응답을 파싱합니다."""
        if "results" not in response:
            raise Exception("잘못된 응답 형식입니다.")
        
        results = response["results"]
        if not results:
            return {
                "text": "",
                "language": "ko",
                "segments": [],
                "speakers": []
            }
        
        # 전체 텍스트 추출
        full_text = ""
        segments = []
        speakers = set()
        
        for utterance in results.get("utterances", []):
            text = utterance.get("msg", "").strip()
            start_time = utterance.get("start_at", 0) / 1000.0  # ms to seconds
            end_time = utterance.get("end_at", 0) / 1000.0
            speaker_id = utterance.get("spk", 0)
            
            if text:
                full_text += text + " "
                segments.append({
                    "start": start_time,
                    "end": end_time,
                    "text": text,
                    "speaker": f"Speaker {speaker_id}"
                })
                speakers.add(f"Speaker {speaker_id}")
        
        return {
            "text": full_text.strip(),
            "language": "ko",
            "segments": segments,
            "speakers": sorted(list(speakers)),
            "duration": max([s["end"] for s in segments]) if segments else 0.0
        }
    
    def get_supported_languages(self) -> List[str]:
        """지원하는 언어 목록을 반환합니다."""
        return ["ko", "en", "ja", "zh", "es", "de", "fr"]
    
    def get_supported_domains(self) -> List[str]:
        """지원하는 도메인 목록을 반환합니다."""
        return ["NEWS", "BUSINESS", "FINANCIAL", "GENERAL"]
    
    def validate_credentials(self) -> bool:
        """API 키가 유효한지 확인합니다."""
        try:
            self._authenticate()
            return True
        except Exception:
            return False


# 편의 함수
def transcribe_with_returnzero(
    file_path: str,
    client_id: str = None,
    client_secret: str = None,
    language: str = "ko",
    use_diarization: bool = True
) -> Dict[str, Any]:
    """
    ReturnZero를 사용하여 오디오 파일을 전사합니다.
    
    Args:
        file_path: 오디오 파일 경로
        client_id: ReturnZero 클라이언트 ID
        client_secret: ReturnZero 클라이언트 시크릿
        language: 언어 코드
        use_diarization: 화자 분리 사용 여부
    
    Returns:
        전사 결과
    """
    client = ReturnZeroSTTClient(client_id, client_secret)
    return client.transcribe(
        file_path, 
        language=language,
        use_diarization=use_diarization
    )