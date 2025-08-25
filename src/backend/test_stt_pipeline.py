"""
STT 결과 → 분석 에이전트 파이프라인 테스트
"""

import asyncio
import logging
from typing import Dict, Any

# 테스트용 더미 데이터
SAMPLE_STT_RESULT = {
    "text": "안녕하세요, 오늘 회의를 시작하겠습니다. 네, 안녕하세요. 반갑습니다.",
    "language": "ko",
    "segments": [
        {
            "start": 4.737,
            "end": 7.097,
            "text": "안녕하세요, 오늘 회의를 시작하겠습니다.",
            "msg": "안녕하세요, 오늘 회의를 시작하겠습니다.",
            "speaker": "Speaker 0",
            "spk": 0,
            "duration": 2.36,
            "language": "ko",
            "confidence": 1.0
        },
        {
            "start": 8.197,
            "end": 11.477,
            "text": "네, 안녕하세요. 반갑습니다.",
            "msg": "네, 안녕하세요. 반갑습니다.",
            "speaker": "Speaker 1", 
            "spk": 1,
            "duration": 3.28,
            "language": "ko", 
            "confidence": 1.0
        }
    ],
    "speakers": ["Speaker 0", "Speaker 1"],
    "speaker_statistics": {
        "Speaker 0": {
            "utterance_count": 1,
            "total_duration": 2.36,
            "total_words": 6
        },
        "Speaker 1": {
            "utterance_count": 1,
            "total_duration": 3.28,
            "total_words": 4
        }
    },
    "duration": 11.477,
    "confidence": 1.0,
    "total_segments": 2,
    "total_speakers": 2
}

SAMPLE_TRANSCRIPT = {
    "segments": SAMPLE_STT_RESULT["segments"],
    "metadata": {
        "total_duration": 11.477,
        "total_segments": 2,
        "speakers_detected": 2,
        "average_confidence": 1.0,
        "language": "ko"
    },
    "full_text": "안녕하세요, 오늘 회의를 시작하겠습니다. 네, 안녕하세요. 반갑습니다.",
    "speaker_summary": {
        "speakers": {
            "Speaker 0": {
                "utterance_count": 1,
                "total_duration": 2.36,
                "total_words": 6
            },
            "Speaker 1": {
                "utterance_count": 1,
                "total_duration": 3.28,
                "total_words": 4
            }
        },
        "total_speakers": 2,
        "total_duration": 5.64,
        "total_words": 10,
        "most_active_speaker": "Speaker 0"
    }
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockMeetingPipeline:
    """테스트용 모의 파이프라인"""
    
    def test_data_mapping(self, transcript: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 매핑 테스트"""
        logger.info("=" * 60)
        logger.info("데이터 매핑 테스트 시작")
        logger.info("=" * 60)
        
        # 화자 정보 올바른 추출
        speaker_summary = transcript.get("speaker_summary", {})
        speakers_list = []
        
        if isinstance(speaker_summary, dict):
            speakers_data = speaker_summary.get("speakers", {})
            if isinstance(speakers_data, dict):
                speakers_list = list(speakers_data.keys())
            elif isinstance(speakers_data, list):
                speakers_list = speakers_data
        
        # 세그먼트 데이터 확인
        segments_data = transcript.get("segments", [])
        
        meeting_data = {
            "transcript": transcript.get("full_text", ""),
            "speakers": speakers_list,
            "timeline": segments_data,
            "segments": segments_data,
            "metadata": transcript.get("metadata", {}),
            "content": transcript.get("full_text", ""),
            "speaker_summary": speaker_summary
        }
        
        # 검증 결과 출력
        logger.info(f"텍스트 길이: {len(meeting_data['transcript'])} 문자")
        logger.info(f"화자 수: {len(meeting_data['speakers'])} 명")
        logger.info(f"화자 목록: {meeting_data['speakers']}")
        logger.info(f"세그먼트 수: {len(meeting_data['timeline'])} 개")
        logger.info(f"메타데이터 키: {list(meeting_data['metadata'].keys())}")
        
        # 화자별 세그먼트 분포 확인
        if meeting_data['timeline']:
            speaker_segments = {}
            for seg in meeting_data['timeline']:
                speaker = seg.get('speaker', 'Unknown')
                speaker_segments[speaker] = speaker_segments.get(speaker, 0) + 1
            logger.info(f"화자별 세그먼트 분포: {speaker_segments}")
        
        # 세그먼트 샘플 확인
        if meeting_data['timeline']:
            sample_segment = meeting_data['timeline'][0]
            logger.info(f"첫 번째 세그먼트 구조: {list(sample_segment.keys())}")
            logger.info(f"첫 번째 세그먼트: {sample_segment}")
        
        logger.info(f"텍스트 내용: {meeting_data['transcript']}")
        logger.info("=" * 60)
        
        return meeting_data


async def test_agent_data_normalization():
    """에이전트 데이터 정규화 테스트"""
    try:
        # BaseAgent import 시도
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from agents.base_agent import BaseAgent
        
        # 테스트용 MockAgent 
        class MockAgent(BaseAgent):
            def __init__(self):
                super().__init__("MockAgent", "테스트용 에이전트")
            
            async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "processed": True,
                    "input_keys": list(input_data.keys()),
                    "transcript_length": len(input_data.get("transcript", "")),
                    "speakers_count": len(input_data.get("speakers", [])),
                    "timeline_count": len(input_data.get("timeline", []))
                }
        
        mock_agent = MockAgent()
        
        logger.info("=" * 60)
        logger.info("에이전트 데이터 정규화 테스트")
        logger.info("=" * 60)
        
        # 테스트 1: 문자열 입력
        result1 = await mock_agent.analyze("안녕하세요, 테스트입니다.")
        logger.info(f"문자열 입력 테스트: {result1}")
        
        # 테스트 2: 딕셔너리 입력 (transcript만)
        test_dict = {"transcript": "딕셔너리 테스트입니다."}
        result2 = await mock_agent.analyze(test_dict)
        logger.info(f"딕셔너리 입력 테스트: {result2}")
        
        # 테스트 3: 실제 파이프라인 데이터 입력
        pipeline = MockMeetingPipeline()
        meeting_data = pipeline.test_data_mapping(SAMPLE_TRANSCRIPT)
        result3 = await mock_agent.analyze(meeting_data)
        logger.info(f"실제 파이프라인 데이터 테스트: {result3}")
        
        logger.info("=" * 60)
        
    except ImportError as e:
        logger.error(f"모듈 import 실패: {e}")
        logger.info("대신 데이터 매핑만 테스트합니다.")
        
        pipeline = MockMeetingPipeline() 
        meeting_data = pipeline.test_data_mapping(SAMPLE_TRANSCRIPT)
        logger.info("데이터 매핑 테스트 완료!")


def main():
    """메인 테스트 실행"""
    logger.info("STT 결과 -> 분석 에이전트 파이프라인 테스트 시작")
    logger.info("=" * 80)
    
    try:
        # 1. 데이터 매핑 테스트
        pipeline = MockMeetingPipeline()
        meeting_data = pipeline.test_data_mapping(SAMPLE_TRANSCRIPT)
        
        # 2. 에이전트 정규화 테스트
        asyncio.run(test_agent_data_normalization())
        
        logger.info("=" * 80)
        logger.info("모든 테스트 완료!")
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()