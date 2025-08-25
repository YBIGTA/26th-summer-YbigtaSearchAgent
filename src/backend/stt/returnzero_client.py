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
        poll_interval = 3  # 3초마다 체크 (API 부하 감소)
        poll_count = 0
        last_status = None
        
        print(f"⏳ 전사 결과 대기 중... (ID: {transcribe_id})")
        print(f"📊 최대 대기 시간: {max_wait_time}초")
        
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(
                    f"{self.base_url}/transcribe/{transcribe_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                
                result = response.json()
                poll_count += 1
                elapsed_time = int(time.time() - start_time)
                
                # 상태 확인
                status = result.get("status")
                
                # 상태가 변경되었거나 5번마다 로그 출력
                if status != last_status or poll_count % 5 == 0:
                    print(f"🔄 [{poll_count}회 확인, {elapsed_time}초 경과] 상태: {status}")
                    last_status = status
                
                if status == "completed":
                    print("✅ 전사 완료!")
                    return result
                elif status == "failed":
                    raise Exception(f"전사 실패: {result.get('message', 'Unknown error')}")
                elif status in ["processing", "waiting", "transcribing"]:
                    # 상태별 메시지 (처음 또는 상태 변경 시에만)
                    if status != last_status:
                        status_messages = {
                            "processing": "🔄 처리 단계로 진입",
                            "waiting": "⏳ 대기열에서 순번 대기",
                            "transcribing": "🎤 음성 인식 진행 중"
                        }
                        print(f"{status_messages.get(status, '🔄 진행 중')}")
                    time.sleep(poll_interval)
                else:
                    # 알 수 없는 상태에 대해서도 계속 진행 (API 업데이트 대응)
                    if status != last_status:
                        print(f"📝 새로운 상태 감지: {status} (계속 진행)")
                    time.sleep(poll_interval)
                    
            except requests.RequestException as e:
                print(f"⚠️ Polling 요청 실패: {e}, 재시도...")
                time.sleep(poll_interval)
                
        final_elapsed = int(time.time() - start_time)
        print(f"⏰ 전사 작업 시간 초과: {final_elapsed}초 경과 (최대 {max_wait_time}초)")
        print(f"📊 총 {poll_count}회 상태 확인, 마지막 상태: {last_status}")
        raise Exception(f"전사 작업 시간 초과 (최대 {max_wait_time}초, 마지막 상태: {last_status})")
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """ReturnZero API 응답을 파싱합니다."""
        print(f"🔍 ReturnZero API 응답 전체: {response}")
        if "results" not in response:
            raise Exception(f"잘못된 응답 형식입니다. 응답 구조: {list(response.keys())}")
        
        results = response["results"]
        print(f"🔍 results 내용: {results}")
        print(f"🔍 results 타입: {type(results)}")
        if not results:
            print("⚠️ results가 비어있습니다!")
            return {
                "text": "",
                "language": "ko",
                "segments": [],
                "speakers": [],
                "duration": 0.0,
                "confidence": 0.0
            }
        
        # 전체 텍스트 추출 및 화자 정보 향상
        full_text = ""
        segments = []
        speakers = set()
        speaker_stats = {}  # 화자별 통계
        
        utterances = results.get("utterances", [])
        print(f"🚨 CRITICAL DEBUG - utterances 개수: {len(utterances)}")
        print(f"🚨 CRITICAL DEBUG - utterances 전체 내용: {utterances}")
        
        # 🔥 CRITICAL FIX: utterances가 비어있는 경우 다른 필드 확인
        if not utterances:
            print("⚠️ utterances가 비어있습니다. 다른 필드 확인...")
            print(f"results 전체 키: {list(results.keys())}")
            
            # 다른 가능한 필드명들 확인
            possible_fields = ['text', 'segments', 'transcripts', 'messages', 'sentences']
            for field in possible_fields:
                if field in results and results[field]:
                    print(f"🔍 대안 필드 발견: {field} = {results[field]}")
        
        # 🔥 CRITICAL: 모든 utterance를 강제로 처리
        processed_count = 0
        for i, utterance in enumerate(utterances):
            print(f"🚨 PROCESSING utterance {i}/{len(utterances)}: {utterance}")
            
            # 🔥 다양한 텍스트 필드명 시도
            text = ""
            text_fields = ["msg", "text", "content", "transcript", "message"]
            for field in text_fields:
                if field in utterance and utterance[field]:
                    text = str(utterance[field]).strip()
                    print(f"✅ 텍스트 추출 성공 ({field}): '{text}'")
                    break
            
            if not text:
                print(f"❌ utterance {i}에서 텍스트를 찾을 수 없음: {list(utterance.keys())}")
                continue
            
            # 시간 정보 추출 (다양한 필드명 지원)
            start_time_ms = utterance.get("start_at", utterance.get("start", 0))
            duration_ms = utterance.get("duration", utterance.get("dur", 0))
            speaker_id = utterance.get("spk", utterance.get("speaker", utterance.get("speaker_id", 0)))
            language = utterance.get("lang", utterance.get("language", "ko"))
            
            print(f"🔍 utterance {i} 정보: text='{text}', speaker={speaker_id}, start={start_time_ms}")
            
            # 시간 변환 (ms -> seconds)
            start_time = start_time_ms / 1000.0 if isinstance(start_time_ms, (int, float)) else 0.0
            end_time = (start_time_ms + duration_ms) / 1000.0 if isinstance(duration_ms, (int, float)) else start_time
            duration_seconds = duration_ms / 1000.0 if isinstance(duration_ms, (int, float)) else 0.0
            
            # 화자 레이블 생성
            speaker_label = f"Speaker {speaker_id}"
            
            # 🔥 CRITICAL: 텍스트 누적 (반드시 실행)
            full_text += text + " "
            processed_count += 1
            print(f"🔥 ACCUMULATED TEXT [{processed_count}]: '{full_text}' (총 길이: {len(full_text)})")
            
            # 세그먼트 정보 생성
            segment = {
                "start": start_time,
                "end": end_time,
                "text": text,
                "msg": text,  # ReturnZero 원본 필드명도 유지
                "speaker": speaker_label,
                "spk": speaker_id,  # 원본 화자 ID도 유지
                "duration": duration_seconds,
                "language": language,
                "confidence": 1.0
            }
            segments.append(segment)
            speakers.add(speaker_label)
            
            # 화자별 통계 수집
            if speaker_label not in speaker_stats:
                speaker_stats[speaker_label] = {
                    "utterance_count": 0,
                    "total_duration": 0.0,
                    "total_words": 0
                }
            
            speaker_stats[speaker_label]["utterance_count"] += 1
            speaker_stats[speaker_label]["total_duration"] += duration_seconds
            speaker_stats[speaker_label]["total_words"] += len(text.split())
        
        print(f"🚨 FINAL PROCESSING SUMMARY:")
        print(f"  - 총 utterances: {len(utterances)}")
        print(f"  - 처리된 utterances: {processed_count}")
        print(f"  - 생성된 segments: {len(segments)}")
        print(f"  - 최종 full_text 길이: {len(full_text)}")
        print(f"  - 최종 full_text 내용: '{full_text.strip()}')")
        
        # 전체 발화 신뢰도 계산 (단순 평균)
        overall_confidence = 1.0 if segments else 0.0
        
        print(f"✅ 파싱 완료: {len(segments)}개 세그먼트, {len(speakers)}명 화자")
        print(f"📊 화자별 통계: {speaker_stats}")
        
        final_full_text = full_text.strip()
        print(f"🔍 DEBUG - 최종 full_text: '{final_full_text}' (길이: {len(final_full_text)})")
        
        # 안전장치: full_text가 비어있으면 segments에서 재생성
        if not final_full_text and segments:
            segment_texts = [seg.get("text", seg.get("msg", "")).strip() for seg in segments if seg.get("text", seg.get("msg", "")).strip()]
            final_full_text = " ".join(segment_texts)
            print(f"🔧 segments에서 재생성된 텍스트: '{final_full_text}' (길이: {len(final_full_text)})")
        
        result = {
            "text": final_full_text,
            "language": "ko",
            "segments": segments,
            "speakers": sorted(list(speakers)),
            "speaker_statistics": speaker_stats,
            "duration": max([s["end"] for s in segments]) if segments else 0.0,
            "confidence": overall_confidence,
            "total_segments": len(segments),
            "total_speakers": len(speakers)
        }
        
        print(f"🔍 DEBUG - 반환되는 결과의 text 길이: {len(result['text'])}")
        return result
    
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