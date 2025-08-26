"""
ChromaDB 벡터 인덱스 관리
벡터 검색, 증분 업데이트 및 문서 갱신 추적 지원
"""

import os
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
try:
    import chromadb
    from chromadb.config import Settings
    from langchain_community.vectorstores import Chroma
    CHROMADB_AVAILABLE = True
except ImportError:
    print("⚠️ ChromaDB not available. Vector indexing disabled.")
    chromadb = None
    Settings = None
    Chroma = None
    CHROMADB_AVAILABLE = False

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ChromaIndexManager:
    def __init__(self, persist_directory: str = "data/indexes/chroma_db"):
        # 환경변수로 경로 오버라이드 허용
        env_dir = os.getenv("CHROMA_PERSIST_DIR")
        if env_dir and os.path.isdir(env_dir):
            persist_directory = env_dir

        self.persist_directory = persist_directory
        self.available = CHROMADB_AVAILABLE
        
        if not self.available:
            print("⚠️ ChromaDB 기능이 비활성화되었습니다.")
            return
        # 환경변수로 컬렉션 이름 오버라이드 허용
        self.collection_name = os.getenv("CHROMA_COLLECTION_NAME", "ybigta_meeting_knowledge")
        self.client = None
        self.vectorstore = None
        self.embeddings = None
        self.collection = None
        
        # 메타데이터 추적용
        self.metadata_file = os.path.join(persist_directory, "document_metadata.json")
        self.document_metadata = self._load_metadata()
        
    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """문서 메타데이터를 로드합니다."""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """문서 메타데이터를 저장합니다."""
        os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.document_metadata, f, ensure_ascii=False, indent=2)
    
    def initialize(self, embeddings):
        """임베딩 모델을 설정하고 ChromaDB를 초기화합니다."""
        if not self.available:
            return
        self.embeddings = embeddings
        
        # ChromaDB 클라이언트 초기화
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 1) 기존 컬렉션 자동 탐지
        try:
            existing = self.client.list_collections()
        except Exception as e:
            existing = []
            print(f"⚠️ 기존 컬렉션 조회 실패: {e}")

        existing_names = [c.name for c in existing] if existing else []

        # 2) 환경변수/기본 이름이 존재하면 그 컬렉션 사용
        if self.collection_name in existing_names:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"✅ 기존 ChromaDB 컬렉션 로드: {self.collection_name}")
        else:
            # 3) 이름이 다르더라도 하나라도 존재하면 '첫 컬렉션'을 채택
            if existing_names:
                picked = existing_names[0]
                self.collection_name = picked
                self.collection = self.client.get_collection(name=picked)
                print(f"✅ 기존 컬렉션 자동 감지 및 사용: {picked}")
            else:
                # 4) 정말 아무 컬렉션도 없을 때만 새로 생성
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "YBIGTA 회의 지식베이스"}
                )
                print(f"📁 새로운 ChromaDB 컬렉션 생성: {self.collection_name}")
        
        # LangChain VectorStore 래퍼 초기화
        self.vectorstore = Chroma(
            client=self.client,
            collection_name=self.collection.name,
            collection_name=self.collection.name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        # 기존 DB 기반으로 메타데이터 재구성
        self._rebuild_metadata_from_chromadb()
    def _rebuild_metadata_from_chromadb(self):
        """ChromaDB에서 실제 데이터를 읽어서 메타데이터를 재구성합니다."""
        if not self.collection:
            print("⚠️ ChromaDB 컬렉션이 초기화되지 않았습니다.")
            return
        
        try:
            # ChromaDB에서 모든 데이터 조회
            results = self.collection.get(
                include=['metadatas', 'documents', 'embeddings']
            )
            
            if not results['ids']:
                print("📭 ChromaDB에 데이터가 없습니다.")
                return
            
            print(f"🔄 ChromaDB에서 {len(results['ids'])}개 문서 발견, 메타데이터 재구성 중...")
            
            # 새로운 메타데이터 딕셔너리 생성
            new_metadata = {}
            
            for i, doc_id in enumerate(results['ids']):
                metadata = results['metadatas'][i] if results['metadatas'] else {}
                document = results['documents'][i] if results['documents'] else ""
                
                # 문서 해시 계산
                content_hash = self._compute_document_hash(document, metadata)
                
                # 메타데이터 구성 (Drive 식별키 보존)
                new_entry = {
                    'content_hash': content_hash,
                    'last_updated': metadata.get('last_updated', datetime.now().isoformat()),
                    'source': metadata.get('source', 'unknown'),
                    'title': metadata.get('title', metadata.get('source', 'Unknown')),
                    'page_id': metadata.get('page_id'),
                    'indexed_at': metadata.get('indexed_at', datetime.now().isoformat())
                }
                # Google Drive 특화 메타 보존
                if metadata.get('source') == 'google_drive':
                    if 'file_id' in metadata:
                        new_entry['file_id'] = metadata.get('file_id')
                    if 'last_modified' in metadata:
                        new_entry['last_modified'] = metadata.get('last_modified')
                    if 'created_time' in metadata:
                        new_entry['created_time'] = metadata.get('created_time')
                
                new_metadata[doc_id] = new_entry
            
            # 기존 메타데이터와 병합 (기존 데이터 우선)
            merged_metadata = {**new_metadata, **self.document_metadata}
            
            # 메타데이터 업데이트
            self.document_metadata = merged_metadata
            self._save_metadata()
            
            print(f"✅ 메타데이터 재구성 완료: {len(merged_metadata)}개 문서")
            
            # 소스별 통계 출력
            source_stats = {}
            for doc_id, meta in merged_metadata.items():
                source = meta.get('source', 'unknown')
                source_stats[source] = source_stats.get(source, 0) + 1
            
            print("📊 소스별 문서 통계:")
            for source, count in source_stats.items():
                print(f"  - {source}: {count}개")
            
        except Exception as e:
            print(f"❌ ChromaDB 메타데이터 재구성 중 오류: {e}")
    
    def _compute_document_hash(self, content: str, metadata: Dict[str, Any]) -> str:
        """문서의 해시값을 계산합니다."""
        # 메타데이터에서 변경 추적에 사용할 키 추출
        hash_content = content + str(metadata.get('source', '')) + str(metadata.get('last_modified', ''))
        return hashlib.sha256(hash_content.encode()).hexdigest()
    
    def _get_document_id(self, source: str, page_id: str = None) -> str:
        """문서의 고유 ID를 생성합니다."""
        if page_id:
            return f"{source}:{page_id}"
        return f"{source}:{hashlib.md5(source.encode()).hexdigest()[:8]}"
    
    def check_document_updates(self, documents: List[Document]) -> Tuple[List[Document], List[str]]:
        """
        문서 업데이트 필요 여부를 확인합니다.
        Returns:
            - new_or_updated_docs: 새롭거나 업데이트된 문서 리스트
            - deleted_doc_ids: 삭제해야 할 문서 ID 리스트
        """
        new_or_updated_docs = []
        current_doc_ids = set()
        
        for doc in documents:
            # 문서 ID 생성
            doc_id = self._get_document_id(
                doc.metadata.get('source', 'unknown'),
                doc.metadata.get('page_id', None)
            )
            current_doc_ids.add(doc_id)
            
            # 문서 해시 계산
            doc_hash = self._compute_document_hash(doc.page_content, doc.metadata)
            
            # 메타데이터에 ID와 해시 추가
            doc.metadata['doc_id'] = doc_id
            doc.metadata['content_hash'] = doc_hash
            doc.metadata['indexed_at'] = datetime.now().isoformat()
            
            # 기존 문서와 비교
            if doc_id in self.document_metadata:
                existing_hash = self.document_metadata[doc_id].get('content_hash')
                if existing_hash != doc_hash:
                    print(f"🔄 업데이트 감지: {doc_id}")
                    new_or_updated_docs.append(doc)
                    self.document_metadata[doc_id] = {
                        'content_hash': doc_hash,
                        'last_updated': datetime.now().isoformat(),
                        'source': doc.metadata.get('source', 'unknown'),
                        'title': doc.metadata.get('title', doc.metadata.get('source', 'Unknown')),
                        'page_id': doc.metadata.get('page_id'),
                        'indexed_at': doc.metadata.get('indexed_at')
                    }
            else:
                print(f"🆕 새 문서 감지: {doc_id}")
                new_or_updated_docs.append(doc)
                self.document_metadata[doc_id] = {
                    'content_hash': doc_hash,
                    'last_updated': datetime.now().isoformat(),
                    'source': doc.metadata.get('source', 'unknown'),
                    'title': doc.metadata.get('title', doc.metadata.get('source', 'Unknown')),
                    'page_id': doc.metadata.get('page_id'),
                    'indexed_at': doc.metadata.get('indexed_at')
                }
        
        # 삭제된 문서 확인 (현재 문서 목록에 없는 기존 문서들)
        # 하단의 '삭제된 문서 확인' 부분을 소스 범위로 한정
        # 그리고 여기서는 '가능성 후보'만 반환하고 실제 삭제 여부는 sync_source에서 full_scan 여부로 결정
        existing_doc_ids = set(self.document_metadata.keys())
        current_doc_ids = set(current_doc_ids)  # 위에서 수집됨
        # 같은 source만 비교
        existing_same_source = {doc_id for doc_id, meta in self.document_metadata.items()
                                if meta.get('source') == (documents[0].metadata.get('source') if documents else None)}
        deleted_doc_ids = list(existing_same_source - current_doc_ids)
        
        if deleted_doc_ids:
            print(f"🗑️ 삭제된 문서 감지: {len(deleted_doc_ids)}개")
            for doc_id in deleted_doc_ids:
                print(f"  - {doc_id}")
        
        return new_or_updated_docs, deleted_doc_ids
    
    def add_documents(self, documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200):
        """문서를 청크로 분할하고 ChromaDB에 추가합니다. (증분 업데이트)"""
        if not self.available:
            print("⚠️ ChromaDB가 비활성화되어 문서 추가를 건너뜁니다.")
            return
        if not documents:
            return
        
        # 업데이트가 필요한 문서 확인
        new_or_updated_docs, deleted_doc_ids = self.check_document_updates(documents)
        
        # 삭제할 문서 처리
        if deleted_doc_ids:
            print(f"🗑️ {len(deleted_doc_ids)}개 문서 삭제 중...")
            for doc_id in deleted_doc_ids:
                try:
                    # ChromaDB에서 문서 삭제
                    self.collection.delete(where={"doc_id": doc_id})
                except Exception as e:
                    print(f"❌ 문서 삭제 실패 {doc_id}: {e}")
        
        # 새 문서나 업데이트된 문서만 처리
        if not new_or_updated_docs:
            print("✅ 업데이트할 문서가 없습니다.")
            return
        
        print(f"📄 {len(new_or_updated_docs)}개 문서 처리 중...")
        
        # 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # 기존 청크 삭제 및 새 청크 추가
        for doc in new_or_updated_docs:
            doc_id = doc.metadata['doc_id']
            
            # 기존 청크 삭제
            try:
                self.collection.delete(where={"doc_id": doc_id})
            except Exception:
                pass  # 새 문서인 경우 삭제할 것이 없음
            
            # 문서를 청크로 분할
            chunks = text_splitter.split_documents([doc])
            
            # 각 청크에 메타데이터 추가
            for i, chunk in enumerate(chunks):
                chunk.metadata['doc_id'] = doc_id
                chunk.metadata['chunk_index'] = i
                chunk.metadata['total_chunks'] = len(chunks)
            
            # ChromaDB에 추가
            if chunks:
                self.vectorstore.add_documents(chunks)
                print(f"✅ {doc_id}: {len(chunks)}개 청크 추가됨")
    
    def sync_source(self, source: str, documents: List[Document], full_scan: bool = False):
        """
        source에서 수집한 documents를 동기화.
        - full_scan=True: 이번 배치가 소스의 '전체 스냅샷'일 때만 기존-현재 차집합을 삭제로 간주
        - full_scan=False: 증분 수집. 삭제는 수행하지 않음.
        """
        if not documents:
            return

        # 기존 코드: 업데이트/신규 판단
        new_or_updated_docs, deleted_doc_ids = self.check_document_updates(documents)

        # 수정: 증분 모드에서는 삭제 금지
        if not full_scan:
            deleted_doc_ids = []

        # 삭제 수행
        if deleted_doc_ids:
            try:
                self.collection.delete(ids=deleted_doc_ids)
                # 메타데이터 삭제 반영
                for did in deleted_doc_ids:
                    self.document_metadata.pop(did, None)
                print(f"🗑️ {len(deleted_doc_ids)}개 문서 삭제 완료")
            except Exception as e:
                print(f"❌ 삭제 중 오류: {e}")

        # 신규/업데이트 문서 upsert
        # (기존 add_documents 등 사용)
        self.add_documents(new_or_updated_docs)
        self._save_metadata()
        
        print(f"✅ {source} 소스 동기화 완료")
    
    def vector_search(self, query: str, top_k: int = 5, filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """벡터 유사도 검색을 수행합니다."""
        if not self.available:
            print("⚠️ ChromaDB가 비활성화되어 빈 결과를 반환합니다.")
            return []
        if not self.vectorstore:
            return []
        
        # 필터 적용
        where_clause = filter if filter else None
        
        results = self.vectorstore.similarity_search_with_score(
            query, 
            k=top_k,
            where=where_clause
        )
        
        return [{
            'document': doc,
            'score': float(score),
            'content': doc.page_content,
            'metadata': doc.metadata,
            'type': 'vector'
        } for doc, score in results]
    
    def metadata_search(self, filter: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """메타데이터 기반 검색을 수행합니다."""
        if not self.collection:
            return []
        
        # ChromaDB 쿼리
        results = self.collection.get(
            where=filter,
            limit=top_k
        )
        
        documents = []
        if results['documents']:
            for i in range(len(results['documents'])):
                doc = Document(
                    page_content=results['documents'][i],
                    metadata=results['metadatas'][i] if results['metadatas'] else {}
                )
                documents.append({
                    'document': doc,
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'type': 'metadata'
                })
        
        return documents
    
    def hybrid_search(self, query: str, top_k: int = 5, filter: Dict[str, Any] = None, vector_weight: float = 0.7) -> List[Dict[str, Any]]:
        """벡터 검색과 메타데이터 검색을 결합한 하이브리드 검색을 수행합니다."""
        # 벡터 검색
        vector_results = self.vector_search(query, top_k * 2, filter)
        
        # 메타데이터 검색 (쿼리 키워드를 포함하는 제목 검색)
        metadata_filter = filter.copy() if filter else {}
        # ChromaDB는 contains 연산자를 지원하지 않으므로 별도 구현 필요
        
        # 결과 병합
        combined_scores = {}
        
        # 벡터 검색 점수 계산
        for i, result in enumerate(vector_results):
            doc_id = result['metadata'].get('doc_id', str(i))
            rank = i + 1
            score = 1 / (60 + rank) * vector_weight
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
        if not self.collection:
            return {"status": "not_initialized"}
        
        # 전체 문서 수
        total_docs = self.collection.count()
        
        # 소스별 문서 수 계산
        source_counts = {}
        update_times = {}
        
        for doc_id, metadata in self.document_metadata.items():
            source = metadata.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
            
            # 최근 업데이트 시간 추적
            last_updated = metadata.get('last_updated')
            if last_updated:
                if source not in update_times or last_updated > update_times[source]:
                    update_times[source] = last_updated
        
        return {
            "status": "initialized",
            "total_documents": len(self.document_metadata),
            "total_chunks": total_docs,
            "source_distribution": source_counts,
            "last_updates": update_times,
            "persist_directory": self.persist_directory
        }
    
    def get_update_status(self) -> Dict[str, Any]:
        """각 소스의 업데이트 상태를 반환합니다."""
        status = {}
        
        for doc_id, metadata in self.document_metadata.items():
            source = metadata.get('source', 'unknown')
            if source not in status:
                status[source] = {
                    'document_count': 0,
                    'last_updated': None,
                    'documents': []
                }
            
            status[source]['document_count'] += 1
            status[source]['documents'].append({
                'id': doc_id,
                'title': metadata.get('title', 'Unknown'),
                'last_updated': metadata.get('last_updated')
            })
            
            # 최신 업데이트 시간 추적
            last_updated = metadata.get('last_updated')
            if last_updated:
                if not status[source]['last_updated'] or last_updated > status[source]['last_updated']:
                    status[source]['last_updated'] = last_updated
        
        return status