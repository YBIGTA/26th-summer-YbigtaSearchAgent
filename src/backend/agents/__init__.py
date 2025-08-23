"""
멀티에이전트 시스템

5가지 전문 에이전트가 협력하여 회의록을 분석합니다:
- AgendaMiner: 핵심 아젠다 추출
- ClaimChecker: 주장-근거 구조 분석
- CounterArguer: 반박 논리 제시  
- EvidenceHunter: 증거 수집 (RAG)
- Summarizer: 결론 및 보고서 작성
"""

from .base_agent import BaseAgent
from .agenda_miner import AgendaMiner
from .claim_checker import ClaimChecker
from .counter_arguer import CounterArguer
from .evidence_hunter import EvidenceHunter
from .summarizer import Summarizer
from .multi_agent_orchestrator import MultiAgentOrchestrator

__all__ = [
    'BaseAgent',
    'AgendaMiner',
    'ClaimChecker', 
    'CounterArguer',
    'EvidenceHunter',
    'Summarizer',
    'MultiAgentOrchestrator'
]