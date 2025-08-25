#!/usr/bin/env python3
"""
RAG 검색 테스트 코드

이 스크립트는 실제 RAG 검색 기능을 테스트하고 문제점을 찾아내기 위해 작성되었습니다.
"""

import os
import sys
import asyncio
from pathlib import Path

# 백엔드 경로 추가
sys.path.append('src/backend')

try:
    from core.embeddings import AsyncUpstageEmbeddings, SyncUpstageEmbeddings
    from indexers.hybrid_chroma_manager import HybridChromaManager
    from agents.simple_analyzer import SimpleMeetingAnalyzer
    from llm import create_upstage_client
    print("✅ 모든 모듈 import 성공")
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    sys.exit(1)

async def test_embeddings():
    """임베딩 클라이언트 테스트"""
    print("\n=== 임베딩 클라이언트 테스트 ===")
    
    try:
        # AsyncUpstageEmbeddings 테스트
        embeddings = AsyncUpstageEmbeddings()
        test_query = "케이터링 서비스"
        
        print(f"테스트 쿼리: '{test_query}'")
        embedding = embeddings.embed_query(test_query)
        
        if embedding:
            print(f"✅ 임베딩 생성 성공: 차원 {len(embedding)}")
            print(f"   첫 5개 값: {embedding[:5]}")
            return embeddings, embedding
        else:
            print("❌ 임베딩 생성 실패")
            return None, None
            
    except Exception as e:
        print(f"❌ 임베딩 테스트 오류: {e}")
        return None, None

def test_chroma_manager():
    """ChromaDB 매니저 테스트"""
    print("\n=== ChromaDB 매니저 테스트 ===")
    
    try:
        chroma_manager = HybridChromaManager()
        print(f"✅ HybridChromaManager 초기화 성공")
        print(f"   Unified DB 사용 가능: {chroma_manager.unified_adapter.available}")
        print(f"   Incremental DB 사용 가능: {chroma_manager.incremental_manager.available}")
        
        if chroma_manager.unified_adapter.available:
            print(f"   Unified 메타데이터 개수: {len(chroma_manager.unified_adapter.virtual_metadata)}")
        
        return chroma_manager
        
    except Exception as e:
        print(f"❌ ChromaDB 매니저 테스트 오류: {e}")
        return None

async def test_vector_search(chroma_manager, embeddings, query_embedding):
    """벡터 검색 테스트"""
    print("\n=== 벡터 검색 테스트 ===")
    
    if not chroma_manager or not embeddings or not query_embedding:
        print("❌ 필수 컴포넌트가 없어 벡터 검색 테스트를 건너뜁니다")
        return None
    
    try:
        test_queries = ["케이터링", "회의", "프로젝트", "업스테이지"]
        
        for query in test_queries:
            print(f"\n--- '{query}' 검색 테스트 ---")
            
            # 임베딩 생성
            query_emb = embeddings.embed_query(query)
            
            # 벡터 검색
            results = chroma_manager.vector_search(
                query=query,
                query_embedding=query_emb,
                top_k=3
            )
            
            if results:
                print(f"✅ 검색 결과 {len(results)}개 발견")
                for i, result in enumerate(results[:2], 1):
                    content = result.get('content', result.get('text', ''))[:100]
                    score = result.get('score', 0.0)
                    metadata = result.get('metadata', {})
                    source = metadata.get('source', 'unknown')
                    print(f"   {i}. [점수: {score:.3f}] [소스: {source}] {content}...")
            else:
                print(f"❌ '{query}' 검색 결과 없음")
        
        return results if results else []
        
    except Exception as e:
        print(f"❌ 벡터 검색 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

async def test_simple_analyzer(chroma_manager, embeddings):
    """SimpleMeetingAnalyzer 테스트"""
    print("\n=== SimpleMeetingAnalyzer 테스트 ===")
    
    if not chroma_manager or not embeddings:
        print("❌ 필수 컴포넌트가 없어 분석기 테스트를 건너뜁니다")
        return
    
    try:
        # LLM 클라이언트 초기화
        llm_client = create_upstage_client()
        
        # SimpleMeetingAnalyzer 초기화
        analyzer = SimpleMeetingAnalyzer(
            llm_client=llm_client,
            chroma_manager=chroma_manager,
            embedding_client=embeddings
        )
        
        print("✅ SimpleMeetingAnalyzer 초기화 성공")
        
        # 테스트 요약 텍스트
        test_summary = """
        회의에서 케이터링 서비스 도입에 대해 논의했습니다.
        비용 효율성과 편의성을 고려해 박스 케이터링을 선택하기로 했습니다.
        업스테이지 해커톤에서 본 케이터링 서비스를 참고하기로 했습니다.
        """
        
        print(f"테스트 요약: {test_summary.strip()}")
        
        # RAG 검색 테스트
        rag_results = analyzer._search_related_documents(test_summary)
        
        if rag_results and "참고 자료를 검색할 수 없습니다" not in rag_results:
            print("✅ RAG 검색 성공:")
            print(rag_results[:500] + "..." if len(rag_results) > 500 else rag_results)
        else:
            print("❌ RAG 검색 실패 또는 결과 없음")
            print(f"반환된 메시지: {rag_results}")
        
    except Exception as e:
        print(f"❌ SimpleMeetingAnalyzer 테스트 오류: {e}")
        import traceback
        traceback.print_exc()

def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("\n=== 데이터베이스 연결 테스트 ===")
    
    # Unified ChromaDB 경로 확인
    unified_path = "data/unified_chroma_db/unified_chroma_db"
    incremental_path = "data/indexes/incremental_chroma_db"
    
    print(f"Unified DB 경로: {unified_path}")
    print(f"  존재 여부: {'✅' if os.path.exists(unified_path) else '❌'}")
    
    if os.path.exists(unified_path):
        files = list(Path(unified_path).glob("*"))
        print(f"  파일 개수: {len(files)}")
        for f in files[:5]:  # 처음 5개만 표시
            print(f"    - {f.name}")
    
    print(f"Incremental DB 경로: {incremental_path}")
    print(f"  존재 여부: {'✅' if os.path.exists(incremental_path) else '❌'}")
    
    # 환경 변수 확인
    print(f"\nUpstage API Key 확인:")
    for i in [''] + [str(j) for j in range(1, 9)]:
        key_name = f'UPSTAGE_API_KEY{i}'
        key_val = os.environ.get(key_name)
        if key_val:
            masked_key = key_val[:8] + "*" * (len(key_val) - 12) + key_val[-4:] if len(key_val) > 12 else "*" * len(key_val)
            print(f"  {key_name}: ✅ {masked_key}")
        else:
            print(f"  {key_name}: ❌ 설정되지 않음")

async def main():
    """메인 테스트 실행"""
    print("🔍 RAG 검색 시스템 종합 테스트 시작\n")
    
    # 1. 기본 환경 확인
    test_database_connection()
    
    # 2. 임베딩 클라이언트 테스트
    embeddings, query_embedding = await test_embeddings()
    
    # 3. ChromaDB 매니저 테스트
    chroma_manager = test_chroma_manager()
    
    # 4. 벡터 검색 테스트
    if chroma_manager and embeddings:
        chroma_manager.initialize(embeddings)
        search_results = await test_vector_search(chroma_manager, embeddings, query_embedding)
    
    # 5. SimpleMeetingAnalyzer 테스트
    await test_simple_analyzer(chroma_manager, embeddings)
    
    print("\n=== 테스트 완료 ===")
    print("위 결과를 확인하여 문제점을 파악하고 수정하세요.")

if __name__ == "__main__":
    asyncio.run(main())