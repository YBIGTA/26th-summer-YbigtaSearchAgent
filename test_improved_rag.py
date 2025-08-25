#!/usr/bin/env python3
"""
개선된 RAG 검색 테스트
"""

import os
import sys
import asyncio
from pathlib import Path

# 백엔드 경로 추가
sys.path.append('src/backend')

from agents.simple_analyzer import SimpleMeetingAnalyzer
from core.embeddings import AsyncUpstageEmbeddings
from indexers.hybrid_chroma_manager import HybridChromaManager
from llm import create_upstage_client

async def test_improved_rag():
    """개선된 RAG 검색 테스트"""
    print("🔍 개선된 RAG 검색 테스트 시작\n")
    
    try:
        # 컴포넌트 초기화
        embeddings = AsyncUpstageEmbeddings()
        chroma_manager = HybridChromaManager()
        chroma_manager.initialize(embeddings)
        llm_client = create_upstage_client()
        
        analyzer = SimpleMeetingAnalyzer(
            llm_client=llm_client,
            chroma_manager=chroma_manager,
            embedding_client=embeddings
        )
        
        print("✅ 모든 컴포넌트 초기화 완료")
        
        # 테스트 요약들
        test_summaries = [
            """
            홈커밍 데이 행사에서 케이터링 서비스 도입을 논의했습니다. 
            비용 효율성과 편의성을 위해 박스 케이터링을 선택하기로 했습니다.
            업스테이지 해커톤에서 본 케이터링 방식을 참고하자는 의견이 나왔습니다.
            """,
            """
            교육 세션 프로세스에 대해 회의했습니다.
            Git과 Python 교육 내용을 준비하고 있으며, 
            발표자들의 검수 과정을 3일 전까지 완료하기로 했습니다.
            """,
            """
            프로젝트 진행 상황을 점검하고 다음 단계를 계획했습니다.
            데이터베이스 연동과 API 개발이 주요 안건이었습니다.
            """
        ]
        
        for i, summary in enumerate(test_summaries, 1):
            print(f"\n=== 테스트 {i} ===")
            print(f"요약: {summary.strip()}")
            
            # 키워드 추출 테스트
            keywords = analyzer._extract_keywords_from_summary(summary)
            print(f"추출된 키워드: {keywords}")
            
            # RAG 검색 테스트
            rag_results = analyzer._search_related_documents(summary)
            
            print(f"RAG 검색 결과:")
            if rag_results and "관련 참고 자료를 찾지 못했습니다" not in rag_results:
                print(rag_results[:800] + "..." if len(rag_results) > 800 else rag_results)
            else:
                print("❌ 관련 자료를 찾지 못했거나 검색 실패")
        
        print("\n=== 테스트 완료 ===")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_improved_rag())