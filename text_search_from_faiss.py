import pickle
import re
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

class FAISSTextSearcher:
    def __init__(self, faiss_index_path: str):
        """FAISS 인덱스에서 텍스트 검색을 수행하는 클래스"""
        self.faiss_index_path = faiss_index_path
        self.documents = []
        self.load_faiss_index()
    
    def load_faiss_index(self):
        """FAISS 인덱스를 로드하고 원본 문서들을 추출합니다."""
        try:
            # FAISS 인덱스 로드
            vectorstore = FAISS.load_local(self.faiss_index_path, allow_dangerous_deserialization=True)
            
            # 원본 문서들 추출
            self.documents = vectorstore.docstore._dict.values()
            print(f"✅ {len(self.documents)}개의 문서를 로드했습니다.")
            
        except Exception as e:
            print(f"❌ FAISS 인덱스 로드 실패: {e}")
            raise
    
    def search_by_text(self, query: str, top_k: int = 5, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """텍스트 기반 검색을 수행합니다."""
        results = []
        
        # 검색어 전처리
        if not case_sensitive:
            query = query.lower()
        
        for doc in self.documents:
            content = doc.page_content
            if not case_sensitive:
                content = content.lower()
            
            # 정확한 단어 매칭
            if query in content:
                # 매칭된 부분의 컨텍스트 추출
                context = self._extract_context(content, query, window_size=100)
                
                results.append({
                    'document': doc,
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'context': context,
                    'match_type': 'exact',
                    'score': 1.0
                })
        
        # 정확도 순으로 정렬
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def search_by_regex(self, pattern: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """정규표현식 기반 검색을 수행합니다."""
        results = []
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            print(f"❌ 정규표현식 오류: {e}")
            return results
        
        for doc in self.documents:
            content = doc.page_content
            matches = regex.findall(content)
            
            if matches:
                # 매칭된 부분의 컨텍스트 추출
                context = self._extract_regex_context(content, regex, window_size=100)
                
                results.append({
                    'document': doc,
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'context': context,
                    'matches': matches,
                    'match_count': len(matches),
                    'match_type': 'regex',
                    'score': len(matches)
                })
        
        # 매칭 개수 순으로 정렬
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def search_by_keywords(self, keywords: List[str], top_k: int = 5, operator: str = 'AND') -> List[Dict[str, Any]]:
        """키워드 기반 검색을 수행합니다."""
        results = []
        
        for doc in self.documents:
            content = doc.page_content.lower()
            score = 0
            
            if operator == 'AND':
                # 모든 키워드가 포함되어야 함
                if all(keyword.lower() in content for keyword in keywords):
                    score = sum(content.count(keyword.lower()) for keyword in keywords)
            elif operator == 'OR':
                # 하나라도 키워드가 포함되면 됨
                score = sum(content.count(keyword.lower()) for keyword in keywords)
            
            if score > 0:
                # 매칭된 키워드들의 컨텍스트 추출
                context = self._extract_keywords_context(content, keywords, window_size=100)
                
                results.append({
                    'document': doc,
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'context': context,
                    'keywords_found': [kw for kw in keywords if kw.lower() in content],
                    'match_type': 'keywords',
                    'score': score
                })
        
        # 점수 순으로 정렬
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _extract_context(self, content: str, query: str, window_size: int = 100) -> str:
        """매칭된 부분 주변의 컨텍스트를 추출합니다."""
        try:
            start_pos = content.find(query)
            if start_pos == -1:
                return content[:window_size] + "..." if len(content) > window_size else content
            
            end_pos = start_pos + len(query)
            
            # 컨텍스트 범위 계산
            context_start = max(0, start_pos - window_size)
            context_end = min(len(content), end_pos + window_size)
            
            context = content[context_start:context_end]
            
            # 컨텍스트 시작/끝 표시
            if context_start > 0:
                context = "..." + context
            if context_end < len(content):
                context = context + "..."
            
            return context
        except Exception as e:
            print(f"⚠️ 컨텍스트 추출 실패: {e}")
            return content[:window_size] + "..." if len(content) > window_size else content
    
    def _extract_regex_context(self, content: str, regex, window_size: int = 100) -> str:
        """정규표현식 매칭 부분의 컨텍스트를 추출합니다."""
        try:
            match = regex.search(content)
            if not match:
                return content[:window_size] + "..." if len(content) > window_size else content
            
            start_pos = match.start()
            end_pos = match.end()
            
            # 컨텍스트 범위 계산
            context_start = max(0, start_pos - window_size)
            context_end = min(len(content), end_pos + window_size)
            
            context = content[context_start:context_end]
            
            # 컨텍스트 시작/끝 표시
            if context_start > 0:
                context = "..." + context
            if context_end < len(content):
                context = context + "..."
            
            return context
        except Exception as e:
            print(f"⚠️ 정규표현식 컨텍스트 추출 실패: {e}")
            return content[:window_size] + "..." if len(content) > window_size else content
    
    def _extract_keywords_context(self, content: str, keywords: List[str], window_size: int = 100) -> str:
        """키워드 매칭 부분의 컨텍스트를 추출합니다."""
        try:
            # 첫 번째 매칭된 키워드 위치 찾기
            first_match_pos = -1
            for keyword in keywords:
                pos = content.find(keyword.lower())
                if pos != -1:
                    first_match_pos = pos
                    break
            
            if first_match_pos == -1:
                return content[:window_size] + "..." if len(content) > window_size else content
            
            # 컨텍스트 범위 계산
            context_start = max(0, first_match_pos - window_size)
            context_end = min(len(content), first_match_pos + window_size)
            
            context = content[context_start:context_end]
            
            # 컨텍스트 시작/끝 표시
            if context_start > 0:
                context = "..." + context
            if context_end < len(content):
                context = context + "..."
            
            return context
        except Exception as e:
            print(f"⚠️ 키워드 컨텍스트 추출 실패: {e}")
            return content[:window_size] + "..." if len(content) > window_size else content

# 사용 예시
if __name__ == "__main__":
    # FAISS 인덱스에서 텍스트 검색
    searcher = FAISSTextSearcher("notion_faiss_index")
    
    # 1. 정확한 텍스트 검색
    print("🔍 정확한 텍스트 검색:")
    results = searcher.search_by_text("YBIGTA", top_k=3)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['metadata'].get('title', '제목 없음')}")
        print(f"   컨텍스트: {result['context']}")
        print()
    
    # 2. 정규표현식 검색
    print("🔍 정규표현식 검색:")
    results = searcher.search_by_regex(r"\b[A-Z]{2,}\b", top_k=3)  # 대문자 단어 검색
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['metadata'].get('title', '제목 없음')}")
        print(f"   매칭: {result['matches'][:5]}")  # 처음 5개만 표시
        print()
    
    # 3. 키워드 검색
    print("🔍 키워드 검색:")
    results = searcher.search_by_keywords(["프로젝트", "개발", "AI"], top_k=3, operator="OR")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['metadata'].get('title', '제목 없음')}")
        print(f"   발견된 키워드: {result['keywords_found']}")
        print() 