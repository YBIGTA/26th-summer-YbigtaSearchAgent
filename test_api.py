#!/usr/bin/env python3
"""
YBIGTA RAG Agent API 테스트 스크립트

FastAPI 서버의 /api/v1/search 엔드포인트를 테스트합니다.
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any, List


class APITester:
    """API 테스트 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.client:
            await self.client.aclose()
    
    async def test_health_check(self) -> bool:
        """헬스 체크 테스트"""
        print("🔍 헬스 체크 테스트 중...")
        try:
            response = await self.client.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 헬스 체크 성공: {data}")
                return True
            else:
                print(f"❌ 헬스 체크 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 헬스 체크 오류: {str(e)}")
            return False
    
    async def test_search_stats(self) -> bool:
        """검색 시스템 통계 테스트"""
        print("\n📊 검색 시스템 통계 테스트 중...")
        try:
            response = await self.client.get(f"{self.base_url}/api/search/stats")
            if response.status_code == 200:
                data = response.json()
                print("✅ 검색 시스템 통계:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return True
            else:
                print(f"❌ 검색 통계 실패: {response.status_code}")
                print(f"응답: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 검색 통계 오류: {str(e)}")
            return False
    
    async def test_search_endpoint(self, test_cases: List[Dict[str, Any]]) -> bool:
        """검색 엔드포인트 테스트"""
        print("\n🔍 검색 엔드포인트 테스트 중...")
        
        success_count = 0
        total_count = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- 테스트 케이스 {i}/{total_count} ---")
            print(f"쿼리: {test_case['query']}")
            print(f"검색 타입: {test_case.get('search_type', 'hybrid')}")
            
            try:
                start_time = time.time()
                response = await self.client.post(
                    f"{self.base_url}/api/v1/search",
                    json=test_case,
                    headers={"Content-Type": "application/json"}
                )
                end_time = time.time()
                
                print(f"응답 시간: {end_time - start_time:.2f}초")
                print(f"상태 코드: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ 검색 성공!")
                    print(f"총 결과 수: {data.get('total_found', 0)}")
                    print(f"응답 시간: {data.get('response_time', 0):.3f}초")
                    
                    # 결과 미리보기
                    results = data.get('results', {})
                    documents = results.get('results', {}).get('documents', [])
                    if documents:
                        print(f"첫 번째 결과: {documents[0][:100]}...")
                    else:
                        print("검색 결과가 없습니다.")
                    
                    success_count += 1
                    
                else:
                    print(f"❌ 검색 실패: {response.status_code}")
                    print(f"응답: {response.text}")
                    
            except Exception as e:
                print(f"❌ 검색 오류: {str(e)}")
        
        print(f"\n📈 테스트 결과: {success_count}/{total_count} 성공")
        return success_count == total_count
    
    async def test_individual_search_types(self) -> bool:
        """개별 검색 타입 테스트"""
        print("\n🎯 개별 검색 타입 테스트 중...")
        
        search_types = [
            {"endpoint": "/api/search/hybrid", "name": "하이브리드 검색"},
            {"endpoint": "/api/search/vector", "name": "벡터 검색"},
            {"endpoint": "/api/search/keyword", "name": "키워드 검색"}
        ]
        
        success_count = 0
        
        for search_type in search_types:
            print(f"\n--- {search_type['name']} 테스트 ---")
            try:
                response = await self.client.post(
                    f"{self.base_url}{search_type['endpoint']}",
                    params={"query": "YBIGTA", "top_k": 3}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {search_type['name']} 성공")
                    print(f"결과 수: {len(data.get('results', {}).get('documents', []))}")
                    success_count += 1
                else:
                    print(f"❌ {search_type['name']} 실패: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {search_type['name']} 오류: {str(e)}")
        
        print(f"\n📊 개별 검색 타입 결과: {success_count}/{len(search_types)} 성공")
        return success_count == len(search_types)


async def main():
    """메인 테스트 함수"""
    print("🚀 YBIGTA RAG Agent API 테스트 시작")
    print("=" * 50)
    
    # 테스트 케이스 정의
    test_cases = [
        {
            "query": "YBIGTA",
            "top_k": 5,
            "search_type": "hybrid"
        },
        {
            "query": "프로젝트",
            "top_k": 3,
            "search_type": "semantic"
        },
        {
            "query": "회의",
            "top_k": 5,
            "search_type": "keyword"
        },
        {
            "query": "AI 분석",
            "top_k": 10,
            "search_type": "hybrid",
            "filters": {"source": "notion"}
        },
        {
            "query": "데이터베이스",
            "top_k": 5,
            "search_type": "hybrid",
            "sources": ["github", "notion"]
        }
    ]
    
    async with APITester() as tester:
        # 1. 헬스 체크
        if not await tester.test_health_check():
            print("❌ 서버가 실행되지 않았습니다. FastAPI 서버를 먼저 시작해주세요.")
            return
        
        # 2. 검색 시스템 통계
        await tester.test_search_stats()
        
        # 3. 통합 검색 엔드포인트 테스트
        search_success = await tester.test_search_endpoint(test_cases)
        
        # 4. 개별 검색 타입 테스트
        individual_success = await tester.test_individual_search_types()
        
        # 최종 결과
        print("\n" + "=" * 50)
        print("🎯 최종 테스트 결과")
        print("=" * 50)
        print(f"통합 검색 API: {'✅ 성공' if search_success else '❌ 실패'}")
        print(f"개별 검색 타입: {'✅ 성공' if individual_success else '❌ 실패'}")
        
        if search_success and individual_success:
            print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        else:
            print("\n⚠️ 일부 테스트가 실패했습니다. 서버 로그를 확인해주세요.")


if __name__ == "__main__":
    # httpx 의존성 확인
    try:
        import httpx
    except ImportError:
        print("❌ httpx 라이브러리가 설치되지 않았습니다.")
        print("다음 명령어로 설치해주세요:")
        print("pip install httpx")
        exit(1)
    
    # 비동기 실행
    asyncio.run(main()) 