#!/usr/bin/env python3
"""
전사 데이터 흐름 디버깅 스크립트
STT 결과부터 Agent까지의 데이터 전달 과정을 추적합니다.
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def simulate_stt_result():
    """STT 결과 시뮬레이션 (ReturnZero API 응답 형식)"""
    return {
        "text": "안녕하세요. 네, 안녕하세요? 반갑습니다.",  # 전체 텍스트
        "language": "ko",
        "segments": [
            {
                "start": 4.737,
                "end": 7.097,
                "text": "안녕하세요.",
                "msg": "안녕하세요.",
                "speaker": "Speaker 0",
                "spk": 0,
                "duration": 2.360,
                "language": "ko",
                "confidence": 1.0
            },
            {
                "start": 8.197,
                "end": 11.477,
                "text": "네, 안녕하세요? 반갑습니다.",
                "msg": "네, 안녕하세요? 반갑습니다.",
                "speaker": "Speaker 1", 
                "spk": 1,
                "duration": 3.280,
                "language": "ko",
                "confidence": 1.0
            }
        ],
        "speakers": ["Speaker 0", "Speaker 1"],
        "duration": 11.477,
        "confidence": 1.0,
        "engine": "returnzero"
    }

def test_pipeline_transcript_generation():
    """Pipeline의 transcript 생성 테스트"""
    
    # Pipeline 코드에서 사용되는 _generate_full_text 함수를 시뮬레이션
    def _generate_full_text(segments):
        """세그먼트에서 전체 텍스트 생성 - 파이프라인과 동일한 로직"""
        print(f"_generate_full_text: 받은 세그먼트 수={len(segments)}")
        if segments:
            print(f"첫 번째 세그먼트 구조: {list(segments[0].keys())}")
            print(f"세그먼트 샘플:")
            for i, seg in enumerate(segments):
                print(f"  {i}: {seg}")
        
        # ReturnZero API 형식에 맞게 msg 필드를 우선 처리
        text_fields = ["msg", "text", "content", "transcript"]
        full_text_parts = []
        empty_segments = 0
        
        for i, seg in enumerate(segments):
            text_content = None
            
            # 우선순위에 따라 텍스트 필드 찾기
            for field in text_fields:
                if field in seg and seg[field] and seg[field].strip():
                    text_content = seg[field].strip()
                    break
            
            if text_content:
                full_text_parts.append(text_content)
                print(f"세그먼트 {i} 텍스트 추가: '{text_content}'")
            else:
                empty_segments += 1
                print(f"세그먼트 {i}에서 텍스트를 찾을 수 없음: {list(seg.keys())}")
                if seg:  # 세그먼트가 비어있지 않다면 내용 출력
                    print(f"  세그먼트 내용: {seg}")
        
        full_text = " ".join(full_text_parts)
        
        print(f"✅ 텍스트 생성 완료: {len(full_text)} 문자, {len(full_text_parts)}개 유효 세그먼트")
        print(f"📊 세그먼트 통계: 전체={len(segments)}, 유효={len(full_text_parts)}, 비어있음={empty_segments}")
        
        if len(full_text) == 0:
            print("🚨 경고: 생성된 전체 텍스트가 비어있습니다!")
            print(f"원본 세그먼트 전체: {segments}")
        else:
            print(f"📝 생성된 전체 텍스트: '{full_text}'")
        
        return full_text

    print("=" * 60)
    print("STT → PIPELINE → AGENT 데이터 흐름 시뮬레이션")
    print("=" * 60)
    
    # 1. STT 결과 시뮬레이션
    print("\n1️⃣ STT 결과 (ReturnZero 응답 시뮬레이션)")
    stt_result = simulate_stt_result()
    print(f"STT 전체 텍스트: '{stt_result['text']}'")
    print(f"STT 세그먼트 수: {len(stt_result['segments'])}")
    for i, seg in enumerate(stt_result['segments']):
        print(f"  세그먼트 {i}: '{seg['text']}' (화자: {seg['speaker']})")
    
    # 2. Pipeline에서 transcript 생성
    print("\n2️⃣ PIPELINE 처리 (_process_transcript 시뮬레이션)")
    segments = stt_result['segments']
    
    # Pipeline의 transcript 구조 생성
    transcript = {
        "segments": segments,
        "metadata": {
            "total_duration": stt_result.get("duration", 0.0),
            "total_segments": len(segments),
            "speakers_detected": len(stt_result.get("speakers", [])),
            "average_confidence": stt_result.get("confidence", 0.0),
            "language": stt_result.get("language", "ko")
        },
        "full_text": _generate_full_text(segments),
        "speaker_summary": {"speakers": {speaker: {"utterance_count": 1} for speaker in stt_result.get("speakers", [])}}
    }
    
    print(f"Pipeline 생성 transcript.full_text: '{transcript['full_text']}'")
    
    # 3. Agent로 전달되는 데이터 시뮬레이션
    print("\n3️⃣ AGENT 전달 데이터 (_process_agents 시뮬레이션)")
    
    # Pipeline에서 Agent로 전달할 때의 처리 로직
    original_transcript = transcript.get("full_text", "").strip()
    print(f"원본 transcript.full_text: '{original_transcript}' (길이: {len(original_transcript)})")
    
    # segments에서 재구성하는 안전장치 로직
    segments_data = transcript.get("segments", [])
    full_text_from_segments = ""
    if segments_data:
        segment_texts = []
        print(f"segments_data에서 텍스트 재구성 시작 ({len(segments_data)}개 세그먼트)")
        for i, seg in enumerate(segments_data):
            text = seg.get("text", seg.get("msg", "")).strip()
            if text:
                segment_texts.append(text)
                print(f"  세그먼트 {i}: '{text}'")
        full_text_from_segments = " ".join(segment_texts)
        print(f"segments에서 재구성된 전체 텍스트: '{full_text_from_segments}' (길이: {len(full_text_from_segments)})")
    
    final_transcript = original_transcript
    if not final_transcript and full_text_from_segments:
        final_transcript = full_text_from_segments
        print("✅ segments에서 재구성된 텍스트 사용")
    
    print(f"🎯 Agent에게 전달될 최종 transcript: '{final_transcript}' (길이: {len(final_transcript)})")
    
    # 4. 결론
    print("\n4️⃣ 결론")
    if len(final_transcript) == 0:
        print("❌ 문제: Agent에게 전달되는 텍스트가 비어있습니다!")
        print("🔍 원인을 파악해야 합니다.")
        return False
    elif len(final_transcript.split()) < 2:
        print("⚠️ 문제: Agent에게 전달되는 텍스트가 너무 짧습니다!")
        print(f"현재: '{final_transcript}' ({len(final_transcript.split())}단어)")
        return False
    else:
        print(f"✅ 정상: Agent에게 전달되는 텍스트가 완전합니다!")
        print(f"전달 텍스트: '{final_transcript}' ({len(final_transcript.split())}단어)")
        return True

if __name__ == "__main__":
    success = test_pipeline_transcript_generation()
    
    if not success:
        print("\n🚨 문제가 발견되었습니다. 실제 코드를 확인해야 합니다.")
        print("가능한 원인:")
        print("1. STT 결과에서 utterances가 제대로 처리되지 않음")
        print("2. Pipeline에서 segments 처리 로직 문제")
        print("3. Agent 전달 시점에서 데이터 손실")
    else:
        print("\n✅ 시뮬레이션에서는 정상 작동합니다.")
        print("실제 코드에서 문제가 있을 수 있으니 실제 STT 결과를 확인해보세요.")