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
        self.client_id = client_id or os.getenv("RETURNZERO_USER_KEY") or os.getenv("RETURNZERO_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("RETURNZERO_USER_SECRET") or os.getenv("RETURNZERO_CLIENT_SECRET")
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
            print(f"🔍 토큰 응답: {data}")
            
            if "access_token" not in data:
                raise Exception(f"access_token을 찾을 수 없습니다. 응답: {data}")
                
            self.jwt_token = data["access_token"]
            
            # 토큰 만료 시간 설정 (API 응답의 expire_at 사용 또는 기본값)
            if "expire_at" in data:
                self.token_expires_at = datetime.fromtimestamp(data["expire_at"])
            else:
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
        
        # 설정 구성 (공식 API 명세에 따라)
        config = {
            "model_name": "sommers",  # 기본 모델
            "use_itn": True,
            "use_diarization": use_diarization,
            "use_paragraph_splitter": True,
            "paragraph_splitter": {
                "max": 50
            },
            "domain": "GENERAL"  # 기본 도메인
        }
        
        # 화자 분리 사용 시 화자 수 설정
        if use_diarization:
            config["diarization"] = {"spk_count": 0}  # 0 = 자동 화자 수 예측
        
        # 언어 설정 (한국어가 아닌 경우만)
        if language != "ko":
            config["language"] = language
        
        # 도메인 설정 (도메인 LM이 아니라 domain 필드)
        if use_domain_lm and domain:
            config["domain"] = domain
        
        try:
            # 1단계: 전사 작업 시작
            with open(audio_file_path, "rb") as audio_file:
                response = requests.post(
                    f"{self.base_url}/transcribe",
                    headers={"Authorization": f"Bearer {token}"},
                    data={"config": json.dumps(config)},
                    files={"file": audio_file}
                )
                if not response.ok:
                    error_detail = response.text
                    print(f"❌ ReturnZero API 에러 응답: {response.status_code}")
                    print(f"❌ 에러 내용: {error_detail}")
                response.raise_for_status()
                
            initial_result = response.json()
            print(f"🔍 ReturnZero 초기 응답: {initial_result}")
            
            # 작업 ID 추출
            if "id" not in initial_result:
                raise Exception(f"작업 ID를 찾을 수 없습니다. 응답: {initial_result}")
                
            transcribe_id = initial_result["id"]
            print(f"📝 전사 작업 ID: {transcribe_id}")
            
            # 2단계: 결과 polling
            result = self._poll_transcription_result(token, transcribe_id)
            return self._parse_response(result)
            
        except requests.RequestException as e:
            raise Exception(f"ReturnZero STT 요청 실패: {e}")
        except FileNotFoundError:
            raise Exception(f"오디오 파일을 찾을 수 없습니다: {audio_file_path}")
    
    def _poll_transcription_result(self, token: str, transcribe_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """전사 결과를 polling하여 가져옵니다."""
        import time
        
        start_time = time.time()
        poll_interval = 2  # 2초마다 체크
        
        print(f"⏳ 전사 결과 대기 중... (ID: {transcribe_id})")
        
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(
                    f"{self.base_url}/transcribe/{transcribe_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                
                result = response.json()
                print(f"🔄 Polling 응답: {result}")
                
                # 상태 확인
                status = result.get("status")
                if status == "completed":
                    print("✅ 전사 완료!")
                    return result
                elif status == "failed":
                    raise Exception(f"전사 실패: {result.get('message', 'Unknown error')}")
                elif status in ["processing", "waiting"]:
                    print(f"🔄 처리 중... 상태: {status}")
                    time.sleep(poll_interval)
                else:
                    print(f"⚠️ 알 수 없는 상태: {status}, 계속 대기...")
                    time.sleep(poll_interval)
                    
            except requests.RequestException as e:
                print(f"⚠️ Polling 요청 실패: {e}, 재시도...")
                time.sleep(poll_interval)
                
        raise Exception(f"전사 작업 시간 초과 (최대 {max_wait_time}초)")
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """ReturnZero API 응답을 파싱합니다."""
        print(f"🔍 ReturnZero API 응답: {response}")
        if "results" not in response:
            raise Exception(f"잘못된 응답 형식입니다. 응답 구조: {list(response.keys())}")
        
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