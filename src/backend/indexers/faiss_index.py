"""
FAISS 벡터 인덱스 관리
벡터 검색 및 하이브리드 검색 지원
"""

import os
import pickle
import re
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class FAISSIndexManager:
    def __init__(self, index_path: str = "data/indexes/faiss_main"):
        self.index_path = index_path
        self.vectorstore = None
        self.embeddings = None
        
    def initialize(self, embeddings):
        """임베딩 모델을 설정하고 인덱스를 로드합니다."""
        self.embeddings = embeddings
        if os.path.exists(self.index_path):
            self.load_index()
        else:
            print(f"📁 새로운 FAISS 인덱스를 생성합니다: {self.index_path}")
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
    
    def load_index(self):
        """기존 FAISS 인덱스를 로드합니다."""
        try:
            self.vectorstore = FAISS.load_local(
                self.index_path, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
            print(f"✅ FAISS 인덱스 로드 완료: {self.index_path}")
        except Exception as e:
            print(f"❌ FAISS 인덱스 로드 실패: {e}")
            raise
    
    def add_documents(self, documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200):
        """문서를 청크로 분할하고 인덱스에 추가합니다."""
        if not documents:
            return
        
        # 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_documents(documents)
        
        print(f"📄 {len(documents)}개 문서를 {len(chunks)}개 청크로 분할")
        
        # 인덱스에 추가
        if self.vectorstore is None:
            self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
        else:
            self.vectorstore.add_documents(chunks)
        
        # 저장
        self.save_index()
        print(f"✅ {len(chunks)}개 청크가 인덱스에 추가됨")
    
    def save_index(self):
        """FAISS 인덱스를 디스크에 저장합니다."""
        if self.vectorstore:
            self.vectorstore.save_local(self.index_path)
            print(f"💾 FAISS 인덱스 저장 완료: {self.index_path}")
    
    def vector_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """벡터 유사도 검색을 수행합니다."""
        if not self.vectorstore:
            return []
        
        results = self.vectorstore.similarity_search_with_score(query, k=top_k)
        
        return [{
            'document': doc,
            'score': float(score),
            'content': doc.page_content,
            'metadata': doc.metadata,
            'type': 'vector'
        } for doc, score in results]
    
    def text_search(self, query: str, top_k: int = 5, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """텍스트 기반 검색을 수행합니다."""
        if not self.vectorstore:
            return []
        
        results = []
        documents = self.vectorstore.docstore._dict.values()
        
        # 검색어 전처리
        if not case_sensitive:
            query = query.lower()
        
        for doc in documents:
            content = doc.page_content
            if not case_sensitive:
                content = content.lower()
            
            if query in content:
                # 매칭 위치 찾기
                indices = [i for i in range(len(content)) if content.startswith(query, i)]
                
                # 컨텍스트 추출
                contexts = []
                for idx in indices[:3]:  # 최대 3개 컨텍스트
                    start = max(0, idx - 50)
                    end = min(len(content), idx + len(query) + 50)
                    context = content[start:end]
                    contexts.append(context)
                
                results.append({
                    'document': doc,
                    'score': len(indices),  # 매칭 횟수를 점수로 사용
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'contexts': contexts,
                    'match_count': len(indices),
                    'type': 'text'
                })
        
        # 점수 순으로 정렬
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def regex_search(self, pattern: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """정규표현식 기반 검색을 수행합니다."""
        if not self.vectorstore:
            return []
        
        results = []
        documents = self.vectorstore.docstore._dict.values()
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            print(f"❌ 정규표현식 오류: {e}")
            return []
        
        for doc in documents:
            matches = regex.findall(doc.page_content)
            
            if matches:
                # 유니크한 매칭 추출
                unique_matches = list(set(matches))[:10]
                
                results.append({
                    'document': doc,
                    'score': len(matches),
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'matches': unique_matches,
                    'match_count': len(matches),
                    'type': 'regex'
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def hybrid_search(self, query: str, top_k: int = 5, vector_weight: float = 0.5) -> List[Dict[str, Any]]:
        """벡터 검색과 텍스트 검색을 결합한 하이브리드 검색을 수행합니다."""
        # 벡터 검색
        vector_results = self.vector_search(query, top_k * 2)
        
        # 텍스트 검색
        text_results = self.text_search(query, top_k * 2)
        
        # 결과 병합 (RRF - Reciprocal Rank Fusion)
        combined_scores = {}
        
        # 벡터 검색 점수 계산
        for i, result in enumerate(vector_results):
            doc_id = id(result['document'])
            rank = i + 1
            score = 1 / (60 + rank) * vector_weight
            combined_scores[doc_id] = {
                'score': score,
                'result': result
            }
        
        # 텍스트 검색 점수 추가
        for i, result in enumerate(text_results):
            doc_id = id(result['document'])
            rank = i + 1
            score = 1 / (60 + rank) * (1 - vector_weight)
            
            if doc_id in combined_scores:
                combined_scores[doc_id]['score'] += score
            else:
                combined_scores[doc_id] = {
                    'score': score,
                    'result': result
                }
        
        # 최종 정렬
        final_results = sorted(
            combined_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:top_k]
        
        return [item['result'] for item in final_results]
    
    def get_statistics(self) -> Dict[str, Any]:
        """인덱스 통계를 반환합니다."""
        if not self.vectorstore:
            return {"status": "not_initialized"}
        
        num_docs = len(self.vectorstore.docstore._dict)
        
        # 소스별 문서 수 계산
        source_counts = {}
        for doc in self.vectorstore.docstore._dict.values():
            source = doc.metadata.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            "status": "initialized",
            "total_documents": num_docs,
            "source_distribution": source_counts,
            "index_path": self.index_path
        }