"""
단순한 2단계 회의 분석 시스템

복잡한 멀티에이전트 시스템을 단순하고 효율적인 2단계 프로세스로 교체:
1단계: 전사 내용 요약 (LLM 요청)
2단계: 요약 + RAG 자료 → 분석/조언/인사이트 도출 (LLM 요청)
"""

from .simple_analyzer import SimpleMeetingAnalyzer

__all__ = [
    'SimpleMeetingAnalyzer'
]