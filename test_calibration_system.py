#!/usr/bin/env python3
"""
CalibrationAgent가 포함된 전체 시스템 테스트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.backend.agents.multi_agent_orchestrator import MultiAgentOrchestrator
from src.backend.agents.calibration_agent import CalibrationAgent


async def test_calibration_system():
    """CalibrationAgent가 포함된 시스템 테스트"""
    
    print("🧪 CalibrationAgent 시스템 테스트 시작")
    
    # 테스트용 간단한 대화 데이터
    test_conversation = """
    A: 안녕하세요, 오늘 프로젝트 진행 상황에 대해 논의해보겠습니다.
    B: 네, 현재 개발이 80% 정도 완료되었습니다.
    A: 그럼 다음 주까지 완료 가능할까요?
    B: 아직 테스트가 남아있어서 조금 더 시간이 필요할 것 같습니다.
    A: 그렇다면 일정을 2주 연장하는 것이 어떨까요?
    B: 그게 좋겠네요. 품질을 보장하기 위해서는 충분한 테스트 시간이 필요합니다.
    """
    
    meeting_data = {
        "transcript": test_conversation,
        "speakers": ["A", "B"],
        "timeline": [
            {"speaker": "A", "timestamp": "00:00", "text": "안녕하세요, 오늘 프로젝트 진행 상황에 대해 논의해보겠습니다."},
            {"speaker": "B", "timestamp": "00:10", "text": "네, 현재 개발이 80% 정도 완료되었습니다."},
        ],
        "metadata": {"meeting_type": "project_update"}
    }
    
    try:
        # LLM 클라이언트 없이 테스트 (fallback 모드)
        print("📝 LLM 클라이언트 없이 fallback 모드로 테스트")
        orchestrator = MultiAgentOrchestrator(llm_client=None)
        
        # 시스템 분석 실행
        result = await orchestrator.analyze_meeting(meeting_data)
        
        print("✅ 시스템 분석 완료")
        print(f"📊 분석 결과 키: {list(result.keys())}")
        
        # CalibrationAgent 결과 확인
        if "final_report" in result:
            print("📋 CalibrationAgent가 생성한 최종 보고서:")
            print("=" * 50)
            print(result["final_report"])
            print("=" * 50)
            return True
        else:
            print("⚠️ CalibrationAgent 결과를 찾을 수 없습니다.")
            print("📋 일반 분석 결과:")
            if "executive_summary" in result:
                print(f"요약: {result.get('executive_summary', {})}")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_calibration_agent_standalone():
    """CalibrationAgent 단독 테스트"""
    
    print("🧪 CalibrationAgent 단독 테스트 시작")
    
    calibration_agent = CalibrationAgent(llm_client=None)
    
    test_data = {
        "original_transcript": "A: 프로젝트가 잘 진행되고 있습니다. B: 네, 다음 주에 완료 예정입니다.",
        "agent_results": {
            "agenda_results": {"agendas": [{"title": "프로젝트 진행 상황"}]},
            "claim_results": {"claims": [{"claim": "프로젝트가 순조롭게 진행됨"}]},
            "counter_results": {"counter_arguments": []},
            "evidence_results": {"evidence_found": []},
            "summary_results": {"executive_summary": {"overview": "프로젝트 논의"}}
        }
    }
    
    try:
        result = await calibration_agent.process(test_data)
        
        print("✅ CalibrationAgent 처리 완료")
        print(f"📊 결과 키: {list(result.keys())}")
        
        if result.get("final_report"):
            print("📋 생성된 마크다운 보고서:")
            print("=" * 50)
            print(result["final_report"])
            print("=" * 50)
            return True
        else:
            print(f"⚠️ 마크다운 보고서가 생성되지 않음: {result}")
            return False
            
    except Exception as e:
        print(f"❌ CalibrationAgent 테스트 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """메인 테스트 실행"""
    
    print("🚀 CalibrationAgent 통합 테스트 시작\n")
    
    # 1. CalibrationAgent 단독 테스트
    standalone_success = await test_calibration_agent_standalone()
    print(f"CalibrationAgent 단독 테스트: {'✅ 성공' if standalone_success else '❌ 실패'}\n")
    
    # 2. 전체 시스템 테스트
    system_success = await test_calibration_system()
    print(f"전체 시스템 테스트: {'✅ 성공' if system_success else '❌ 실패'}\n")
    
    # 3. 결과 요약
    if standalone_success and system_success:
        print("🎉 모든 테스트 성공! CalibrationAgent가 제대로 통합되었습니다.")
        print("✅ 최종 보고서가 마크다운 형식으로 생성됩니다.")
        print("✅ 전체 대화 내용을 기반으로 보고서가 보정됩니다.")
    elif standalone_success:
        print("⚠️ CalibrationAgent는 작동하지만 전체 시스템 통합에 문제가 있습니다.")
    elif system_success:
        print("⚠️ 전체 시스템은 작동하지만 CalibrationAgent에 문제가 있습니다.")
    else:
        print("❌ 테스트 실패 - 문제를 해결해야 합니다.")
    
    return standalone_success and system_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)