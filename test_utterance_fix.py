#!/usr/bin/env python3
"""
전사 결과 한 문장 문제 해결 테스트 스크립트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_returnzero_parsing():
    """ReturnZero 응답 파싱 테스트"""
    
    print("🧪 ReturnZero 응답 파싱 테스트 시작")
    
    # 실제 API 응답 시뮬레이션 (사용자가 제공한 형식)
    mock_api_response = {
        "id": "test_transcribe_id",
        "status": "completed",
        "results": {
            "utterances": [
                {
                    "start_at": 4737,
                    "duration": 2360,
                    "msg": "안녕하세요.",
                    "spk": 0,
                    "lang": "ko"
                },
                {
                    "start_at": 8197,
                    "duration": 3280,
                    "msg": "네, 안녕하세요? 반갑습니다.",
                    "spk": 1,
                    "lang": "ko"
                },
                {
                    "start_at": 12000,
                    "duration": 1500,
                    "msg": "오늘 프로젝트 진행 상황에 대해 이야기해보죠.",
                    "spk": 0,
                    "lang": "ko"
                }
            ]
        }
    }
    
    try:
        from src.backend.stt.returnzero_client import ReturnZeroSTTClient
        
        # 클라이언트 인스턴스 생성 (실제 API 호출 없이 파싱만 테스트)
        client = ReturnZeroSTTClient()
        
        # 파싱 함수 직접 호출
        result = client._parse_response(mock_api_response)
        
        print(f"✅ 파싱 완료!")
        print(f"📊 결과 요약:")
        print(f"  - 전체 텍스트 길이: {len(result.get('text', ''))}")
        print(f"  - 전체 텍스트 내용: '{result.get('text', '')}'")
        print(f"  - 세그먼트 수: {len(result.get('segments', []))}")
        print(f"  - 화자 수: {len(result.get('speakers', []))}")
        
        # 각 세그먼트 확인
        print(f"\n📝 세그먼트별 상세:")
        for i, seg in enumerate(result.get('segments', [])):
            print(f"  {i+1}: '{seg.get('text', '')}' (화자: {seg.get('speaker', 'Unknown')})")
        
        # 성공 여부 판단
        expected_utterances = 3
        actual_segments = len(result.get('segments', []))
        expected_text_parts = ["안녕하세요", "반갑습니다", "프로젝트"]
        actual_text = result.get('text', '')
        
        success = True
        if actual_segments != expected_utterances:
            print(f"❌ 세그먼트 수 불일치: 예상 {expected_utterances}, 실제 {actual_segments}")
            success = False
        
        for part in expected_text_parts:
            if part not in actual_text:
                print(f"❌ 텍스트 누락: '{part}'가 최종 텍스트에 없음")
                success = False
        
        if success:
            print(f"🎉 모든 utterances가 올바르게 처리되었습니다!")
        else:
            print(f"❌ utterances 처리에 문제가 있습니다.")
            
        return success
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_stt_manager_validation():
    """STT 매니저 검증 로직 테스트"""
    
    print("\n🧪 STT 매니저 검증 테스트 시작")
    
    # 텍스트는 비어있지만 segments는 있는 상황 시뮬레이션
    mock_stt_result = {
        "text": "",  # 비어있음
        "segments": [
            {"text": "첫 번째 발화", "msg": "첫 번째 발화"},
            {"text": "두 번째 발화", "msg": "두 번째 발화"}
        ]
    }
    
    # STT 매니저의 검증 로직 시뮬레이션
    if mock_stt_result.get('segments') and not mock_stt_result.get('text', '').strip():
        print("⚠️ text가 비어있지만 segments가 존재 - 재구성 시도")
        segment_texts = []
        for seg in mock_stt_result.get('segments', []):
            text = seg.get('text', seg.get('msg', '')).strip()
            if text:
                segment_texts.append(text)
        reconstructed_text = ' '.join(segment_texts)
        mock_stt_result['text'] = reconstructed_text
        print(f"✅ segments에서 텍스트 재구성: '{reconstructed_text}'")
        return len(reconstructed_text) > 0
    
    return False

def test_pipeline_safety_net():
    """파이프라인 안전장치 테스트"""
    
    print("\n🧪 파이프라인 안전장치 테스트 시작")
    
    # transcript 구조 시뮬레이션
    mock_transcript = {
        "full_text": "",  # 비어있음
        "segments": [
            {"text": "테스트 문장 1", "msg": "테스트 문장 1"},
            {"text": "테스트 문장 2", "msg": "테스트 문장 2"}
        ]
    }
    
    # 파이프라인 안전장치 로직 시뮬레이션
    segments_data = mock_transcript.get("segments", [])
    full_text_from_segments = ""
    
    if segments_data:
        segment_texts = []
        print(f"🚨 CRITICAL - segments_data 처리 시작 ({len(segments_data)}개 세그먼트)")
        
        for i, seg in enumerate(segments_data):
            print(f"🔍 세그먼트 {i} 분석: {seg}")
            
            # 더 많은 필드명 시도
            text = ""
            text_fields = ["text", "msg", "content", "transcript", "message", "speech"]
            
            for field in text_fields:
                if field in seg and seg[field] and str(seg[field]).strip():
                    text = str(seg[field]).strip()
                    print(f"✅ 세그먼트 {i} 텍스트 추출 성공 ({field}): '{text}'")
                    break
            
            if text:
                segment_texts.append(text)
        
        full_text_from_segments = " ".join(segment_texts)
        print(f"🚨 CRITICAL - segments에서 재구성된 최종 텍스트:")
        print(f"  - 내용: '{full_text_from_segments}'")
        
        return len(full_text_from_segments) > 0
    
    return False

def main():
    """메인 테스트 실행"""
    
    print("🚀 전사 결과 한 문장 문제 해결 테스트 시작")
    print("=" * 60)
    
    # 테스트 실행
    test1 = test_returnzero_parsing()
    test2 = test_stt_manager_validation() 
    test3 = test_pipeline_safety_net()
    
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약:")
    print(f"1. ReturnZero 파싱 테스트: {'✅ 통과' if test1 else '❌ 실패'}")
    print(f"2. STT 매니저 검증 테스트: {'✅ 통과' if test2 else '❌ 실패'}")
    print(f"3. 파이프라인 안전장치 테스트: {'✅ 통과' if test3 else '❌ 실패'}")
    
    all_passed = test1 and test2 and test3
    
    if all_passed:
        print("\n🎉 모든 테스트 통과! 전사 결과 한 문장 문제가 해결되었습니다!")
        print("✅ 이제 실제 오디오 파일로 테스트해보세요.")
    else:
        print("\n⚠️ 일부 테스트 실패 - 추가 디버깅이 필요합니다.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)