"""
화자 분리 시스템 (Speaker Diarization)

pyannote.audio를 사용한 고급 화자 분리 기능을 제공합니다.
- 실시간 화자 식별
- 다중 화자 분리
- 타임라인 기반 발화 분석
- STT 결과와의 정밀 매칭
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SpeakerDiarizationEngine:
    """화자 분리 엔진 클래스"""
    
    def __init__(self, use_pyannote: bool = True, huggingface_token: Optional[str] = None):
        self.use_pyannote = use_pyannote
        self.huggingface_token = huggingface_token or os.getenv("HUGGINGFACE_TOKEN")
        self.pipeline = None
        self._initialize_pipeline()
        
        # 화자 매핑 캐시
        self.speaker_embeddings = {}
        self.speaker_names = {}  # 사용자 정의 화자명
        
        # 성능 통계
        self.stats = {
            "total_diarizations": 0,
            "avg_speakers_detected": 0.0,
            "avg_processing_time": 0.0,
            "pyannote_success_rate": 0.0
        }
    
    def _initialize_pipeline(self):
        """pyannote 파이프라인 초기화"""
        if not self.use_pyannote:
            logger.info("화자 분리: 기본 모드 사용")
            return
        
        try:
            from pyannote.audio import Pipeline
            if self.huggingface_token:
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization",
                    use_auth_token=self.huggingface_token
                )
                logger.info("pyannote.audio 파이프라인 초기화 완료")
            else:
                logger.warning("HUGGINGFACE_TOKEN이 설정되지 않았습니다. 기본 모드로 전환합니다.")
                self.use_pyannote = False
        except Exception as e:
            logger.error(f"pyannote.audio 초기화 실패: {str(e)}")
            self.use_pyannote = False
    
    async def diarize_audio(self, audio_path: str, stt_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """오디오 파일에서 화자 분리 수행"""
        start_time = datetime.now()
        
        try:
            if self.use_pyannote and self.pipeline:
                diarization_result = await self._diarize_with_pyannote(audio_path)
                speakers_detected = len(set(seg.get("speaker", "") for seg in diarization_result))
                self.stats["pyannote_success_rate"] = min(self.stats["pyannote_success_rate"] + 0.1, 1.0)
            else:
                diarization_result = self._diarize_fallback(stt_segments)
                speakers_detected = 1
            
            # STT 세그먼트와 매칭
            aligned_segments = await self._align_segments(stt_segments, diarization_result)
            
            # 후처리: 연속된 같은 화자 병합
            processed_segments = await self._post_process_segments(aligned_segments)
            
            # 통계 업데이트
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(speakers_detected, processing_time)
            
            logger.info(f"화자 분리 완료: {speakers_detected}명 화자, {processing_time:.2f}초")
            return processed_segments
            
        except Exception as e:
            logger.error(f"화자 분리 오류: {str(e)}")
            return self._diarize_fallback(stt_segments)
    
    async def _diarize_with_pyannote(self, audio_path: str) -> List[Dict[str, Any]]:
        """pyannote를 사용한 화자 분리"""
        try:
            # 비동기 실행을 위해 executor 사용
            loop = asyncio.get_event_loop()
            diarization = await loop.run_in_executor(None, self.pipeline, audio_path)
            
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start": float(turn.start),
                    "end": float(turn.end),
                    "speaker": str(speaker),
                    "confidence": 0.9  # pyannote는 일반적으로 높은 신뢰도
                })
            
            return segments
            
        except Exception as e:
            logger.error(f"pyannote 화자 분리 실패: {str(e)}")
            raise
    
    def _diarize_fallback(self, stt_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """폴백 화자 분리 (단일 화자)"""
        segments = []
        for s in stt_segments:
            segments.append({
                "start": float(s.get("start", 0.0)),
                "end": float(s.get("end", 0.0)),
                "speaker": "Speaker 1",
                "confidence": 0.5  # 낮은 신뢰도
            })
        return segments

    async def _align_segments(self, stt_segments: List[Dict[str, Any]], diarization_result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """STT 세그먼트와 화자 분리 결과 정렬"""
        aligned = []
        
        for stt_seg in stt_segments:
            start_time = float(stt_seg.get("start", 0.0))
            end_time = float(stt_seg.get("end", 0.0))
            center_time = (start_time + end_time) / 2.0
            
            # 중심 시간이 포함된 화자 구간 찾기
            best_speaker = "Unknown"
            best_confidence = 0.0
            
            for dia_seg in diarization_result:
                dia_start = dia_seg.get("start", 0.0)
                dia_end = dia_seg.get("end", 0.0)
                
                # 겹치는 구간이 있는지 확인
                overlap_start = max(start_time, dia_start)
                overlap_end = min(end_time, dia_end)
                
                if overlap_start < overlap_end:
                    # 겹치는 비율 계산
                    overlap_duration = overlap_end - overlap_start
                    stt_duration = end_time - start_time
                    overlap_ratio = overlap_duration / stt_duration if stt_duration > 0 else 0
                    
                    confidence = dia_seg.get("confidence", 0.5) * overlap_ratio
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_speaker = dia_seg.get("speaker", "Unknown")
            
            # 사용자 정의 화자명으로 변환
            display_speaker = self.speaker_names.get(best_speaker, best_speaker)
            
            aligned.append({
                **stt_seg,
                "speaker": display_speaker,
                "speaker_confidence": best_confidence,
                "timestamp": start_time,
                "duration": end_time - start_time
            })
        
        return aligned

    async def _post_process_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """후처리: 연속된 같은 화자 세그먼트 병합 및 정리"""
        if not segments:
            return segments
        
        processed = []
        current_segment = None
        
        for segment in segments:
            speaker = segment.get("speaker")
            text = segment.get("text", "")
            
            if current_segment is None:
                current_segment = segment.copy()
            elif current_segment.get("speaker") == speaker:
                # 같은 화자의 연속 발화 - 병합
                current_segment["text"] = (current_segment.get("text", "") + " " + text).strip()
                current_segment["end"] = segment.get("end", current_segment["end"])
                current_segment["duration"] = current_segment["end"] - current_segment["start"]
            else:
                # 다른 화자 - 이전 세그먼트 저장하고 새로 시작
                if current_segment.get("text", "").strip():
                    processed.append(current_segment)
                current_segment = segment.copy()
        
        # 마지막 세그먼트 추가
        if current_segment and current_segment.get("text", "").strip():
            processed.append(current_segment)
        
        # 발화 번호 추가
        for i, segment in enumerate(processed):
            segment["utterance_id"] = i + 1
        
        return processed
    
    def set_speaker_names(self, speaker_mapping: Dict[str, str]):
        """화자 ID를 실제 이름으로 매핑"""
        self.speaker_names.update(speaker_mapping)
        logger.info(f"화자명 매핑 설정: {speaker_mapping}")
    
    def _update_stats(self, speakers_detected: int, processing_time: float):
        """통계 업데이트"""
        self.stats["total_diarizations"] += 1
        total = self.stats["total_diarizations"]
        
        # 평균 화자 수 업데이트
        current_avg_speakers = self.stats["avg_speakers_detected"]
        self.stats["avg_speakers_detected"] = (current_avg_speakers * (total - 1) + speakers_detected) / total
        
        # 평균 처리 시간 업데이트
        current_avg_time = self.stats["avg_processing_time"]
        self.stats["avg_processing_time"] = (current_avg_time * (total - 1) + processing_time) / total
    
    def get_stats(self) -> Dict[str, Any]:
        """화자 분리 통계 반환"""
        return {
            **self.stats,
            "pyannote_enabled": self.use_pyannote and self.pipeline is not None,
            "speaker_mappings": len(self.speaker_names),
            "configuration": {
                "use_pyannote": self.use_pyannote,
                "has_token": bool(self.huggingface_token)
            }
        }
    
    def analyze_speaker_distribution(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """화자별 발화 분석"""
        speaker_stats = {}
        total_duration = 0.0
        
        for segment in segments:
            speaker = segment.get("speaker", "Unknown")
            duration = segment.get("duration", 0.0)
            text = segment.get("text", "")
            
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    "utterance_count": 0,
                    "total_duration": 0.0,
                    "word_count": 0,
                    "avg_utterance_length": 0.0
                }
            
            speaker_stats[speaker]["utterance_count"] += 1
            speaker_stats[speaker]["total_duration"] += duration
            speaker_stats[speaker]["word_count"] += len(text.split())
            total_duration += duration
        
        # 비율 계산
        for speaker, stats in speaker_stats.items():
            if stats["utterance_count"] > 0:
                stats["avg_utterance_length"] = stats["total_duration"] / stats["utterance_count"]
            if total_duration > 0:
                stats["speaking_ratio"] = stats["total_duration"] / total_duration
        
        return {
            "total_speakers": len(speaker_stats),
            "total_duration": total_duration,
            "speaker_stats": speaker_stats,
            "most_active_speaker": max(speaker_stats.keys(), key=lambda s: speaker_stats[s]["total_duration"]) if speaker_stats else None
        }


# 편의 함수들 (하위 호환성)
def diarize_segments_mvp(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """기본 화자 분리 (모든 발화를 Speaker 1로 지정)"""
    engine = SpeakerDiarizationEngine(use_pyannote=False)
    return engine._diarize_fallback(segments)


async def assign_speakers(
    audio_path: str,
    stt_segments: List[Dict[str, Any]],
    prefer_pyannote: bool = True,
    speaker_names: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """STT 세그먼트에 화자 정보 할당"""
    engine = SpeakerDiarizationEngine(use_pyannote=prefer_pyannote)
    
    if speaker_names:
        engine.set_speaker_names(speaker_names)
    
    return await engine.diarize_audio(audio_path, stt_segments)