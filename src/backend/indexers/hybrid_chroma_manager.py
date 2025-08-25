"""
HybridChromaManager - 기존 unified_chroma_db + 새로운 증분 데이터 통합 관리

- unified_chroma_db: 읽기 전용으로 기존 데이터 활용
- incremental_chroma_db: 새로운 변경사항만 관리
- 검색 시 두 DB 결과를 투명하게 병합
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from langchain_core.documents import Document

from .unified_chroma_adapter import UnifiedChromaAdapter
from .chroma_index import ChromaIndexManager


class HybridChromaManager:
    """Unified + Incremental ChromaDB 하이브리드 관리자"""
    
    def __init__(self, 
                 unified_db_path: str = "data/unified_chroma_db/unified_chroma_db",
                 incremental_db_path: str = "data/indexes/incremental_chroma_db"):
        
        # 어댑터 초기화 (기존 데이터용)
        self.unified_adapter = UnifiedChromaAdapter(unified_db_path)
        
        # 증분 매니저 초기화 (새 데이터용) 
        self.incremental_manager = ChromaIndexManager(incremental_db_path)
        
        # 외부 메타데이터 관리
        self.external_metadata_file = os.path.join(
            os.path.dirname(incremental_db_path), "hybrid_document_metadata.json"
        )
        self.hybrid_metadata = self._load_hybrid_metadata()
        
        self.available = self.unified_adapter.available or self.incremental_manager.available
        
        print(f"🔗 하이브리드 ChromaDB 초기화")
        print(f"  - Unified DB: {'✅' if self.unified_adapter.available else '❌'}")
        print(f"  - Incremental DB: {'준비됨' if self.incremental_manager.available else '❌'}")
    
    def initialize(self, embeddings):
        """임베딩 모델 설정 및 시스템 초기화"""
        print("🚀 하이브리드 ChromaDB 시스템 초기화 중...")
        
        # 증분 매니저 초기화
        if self.incremental_manager.available:
            self.incremental_manager.initialize(embeddings)
        
        # 통합 메타데이터 생성
        self._merge_metadata_sources()
        
        print("✅ 하이브리드 ChromaDB 시스템 초기화 완료")
    
    def _load_hybrid_metadata(self) -> Dict[str, Dict[str, Any]]:
        """하이브리드 메타데이터 로드"""
        if os.path.exists(self.external_metadata_file):
            try:
                with open(self.external_metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 하이브리드 메타데이터 로드 실패: {e}")
        return {}
    
    def _save_hybrid_metadata(self):
        """하이브리드 메타데이터 저장"""
        try:
            os.makedirs(os.path.dirname(self.external_metadata_file), exist_ok=True)
            with open(self.external_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.hybrid_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 하이브리드 메타데이터 저장 실패: {e}")
    
    def _merge_metadata_sources(self):
        """unified + incremental 메타데이터 통합"""
        print("🔄 메타데이터 소스 통합 중...")
        
        # Unified DB 메타데이터 병합
        if self.unified_adapter.available:
            unified_metadata = self.unified_adapter.get_virtual_metadata()
            for doc_id, metadata in unified_metadata.items():
                if doc_id not in self.hybrid_metadata:
                    self.hybrid_metadata[doc_id] = {
                        **metadata,
                        'storage': 'unified',
                        'last_synced': datetime.now().isoformat()
                    }
        
        # Incremental DB 메타데이터 병합
        if (hasattr(self.incremental_manager, 'document_metadata') and 
            self.incremental_manager.document_metadata):
            for doc_id, metadata in self.incremental_manager.document_metadata.items():
                self.hybrid_metadata[doc_id] = {
                    **metadata,
                    'storage': 'incremental',
                    'last_synced': datetime.now().isoformat()
                }
        
        # 통합 메타데이터 저장
        self._save_hybrid_metadata()
        
        print(f"✅ 총 {len(self.hybrid_metadata)}개 문서 메타데이터 통합 완료")
    
    def check_document_updates(self, documents: List[Document]) -> Tuple[List[Document], List[str]]:
        """하이브리드 환경에서 문서 업데이트 확인"""
        new_or_updated_docs = []
        deleted_doc_ids = []
        current_doc_ids = set()
        
        for doc in documents:
            # 문서 ID 생성 (기존 방식 유지)
            source = doc.metadata.get('source', 'unknown')
            page_id = doc.metadata.get('page_id', None)
            
            if page_id:
                doc_id = f"{source}:{page_id}"
            else:
                doc_id = f"{source}:{hashlib.md5(source.encode()).hexdigest()[:8]}"
            
            current_doc_ids.add(doc_id)
            
            # 문서 해시 계산
            hash_content = doc.page_content + str(source) + str(doc.metadata.get('last_modified', ''))
            doc_hash = hashlib.sha256(hash_content.encode()).hexdigest()
            
            # 메타데이터에 ID와 해시 추가
            doc.metadata['doc_id'] = doc_id
            doc.metadata['content_hash'] = doc_hash
            doc.metadata['indexed_at'] = datetime.now().isoformat()
            
            # 기존 문서와 비교
            if doc_id in self.hybrid_metadata:
                existing_hash = self.hybrid_metadata[doc_id].get('content_hash')
                existing_storage = self.hybrid_metadata[doc_id].get('storage', 'unified')
                
                if existing_hash != doc_hash:
                    print(f"🔄 업데이트 감지: {doc_id} (기존: {existing_storage})")
                    new_or_updated_docs.append(doc)
                    
                    # 메타데이터 업데이트
                    self.hybrid_metadata[doc_id] = {
                        'content_hash': doc_hash,
                        'last_updated': datetime.now().isoformat(),
                        'source': doc.metadata.get('source'),
                        'title': doc.metadata.get('title', 'Unknown'),
                        'storage': 'incremental',  # 업데이트된 문서는 incremental로 이동
                        'previous_storage': existing_storage
                    }
            else:
                print(f"➕ 새 문서 감지: {doc_id}")
                new_or_updated_docs.append(doc)
                
                # 새 문서 메타데이터 추가
                self.hybrid_metadata[doc_id] = {
                    'content_hash': doc_hash,
                    'last_updated': datetime.now().isoformat(),
                    'source': doc.metadata.get('source'),
                    'title': doc.metadata.get('title', 'Unknown'),
                    'storage': 'incremental'
                }
        
        # 삭제된 문서 찾기 (현재 소스에서)
        if documents:
            source = documents[0].metadata.get('source')
            if source:
                for doc_id, metadata in list(self.hybrid_metadata.items()):
                    if (metadata.get('source') == source and 
                        doc_id not in current_doc_ids):
                        print(f"➖ 삭제 감지: {doc_id}")
                        deleted_doc_ids.append(doc_id)
                        del self.hybrid_metadata[doc_id]
        
        # 메타데이터 저장
        self._save_hybrid_metadata()
        
        return new_or_updated_docs, deleted_doc_ids
    
    def add_documents(self, documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200):
        """문서를 증분 DB에 추가"""
        if not documents:
            return
        
        print(f"📄 하이브리드 시스템에 {len(documents)}개 문서 추가 중...")
        
        # 업데이트가 필요한 문서 확인
        new_or_updated_docs, deleted_doc_ids = self.check_document_updates(documents)
        
        # 증분 매니저를 통해 추가
        if self.incremental_manager.available and new_or_updated_docs:
            self.incremental_manager.add_documents(new_or_updated_docs, chunk_size, chunk_overlap)
        
        # 삭제 처리 (incremental DB에서만)
        if deleted_doc_ids and self.incremental_manager.collection:
            for doc_id in deleted_doc_ids:
                try:
                    self.incremental_manager.collection.delete(where={"doc_id": doc_id})
                    print(f"🗑️ 문서 삭제: {doc_id}")
                except Exception as e:
                    print(f"❌ 문서 삭제 실패 {doc_id}: {e}")
    
    def vector_search(self, query: str, top_k: int = 5, filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """하이브리드 벡터 검색 (unified + incremental)"""
        all_results = []
        
        # Unified DB 검색
        if self.unified_adapter.available:
            try:
                unified_results = self.unified_adapter.search_documents(query, top_k)
                all_results.extend(unified_results)
            except Exception as e:
                print(f"⚠️ Unified DB 검색 오류: {e}")
        
        # Incremental DB 검색
        if self.incremental_manager.available:
            try:
                incremental_results = self.incremental_manager.vector_search(query, top_k, filter)
                all_results.extend(incremental_results)
            except Exception as e:
                print(f"⚠️ Incremental DB 검색 오류: {e}")
        
        # 결과 점수 기준 정렬 및 중복 제거
        unique_results = {}
        for result in all_results:
            doc_id = result.get('metadata', {}).get('doc_id')
            if doc_id:
                # 높은 점수의 결과만 유지
                if doc_id not in unique_results or result['score'] > unique_results[doc_id]['score']:
                    unique_results[doc_id] = result
        
        # 점수 순 정렬 후 상위 k개 반환
        sorted_results = sorted(unique_results.values(), key=lambda x: x['score'], reverse=True)
        return sorted_results[:top_k]
    
    def sync_source(self, source: str, documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200):
        """특정 소스 동기화 (증분 DB로)"""
        print(f"🔄 하이브리드 시스템 - {source} 소스 동기화 시작...")
        
        # 소스별로 문서 메타데이터 업데이트
        for doc in documents:
            doc.metadata['source'] = source
            doc.metadata['sync_timestamp'] = datetime.now().isoformat()
        
        # 문서 추가/업데이트
        self.add_documents(documents, chunk_size, chunk_overlap)
        
        print(f"✅ {source} 소스 동기화 완료")
    
    def get_statistics(self) -> Dict[str, Any]:
        """하이브리드 시스템 통계"""
        stats = {
            "status": "hybrid_initialized",
            "unified_available": self.unified_adapter.available,
            "incremental_available": self.incremental_manager.available,
            "total_documents": len(self.hybrid_metadata),
            "storage_distribution": {}
        }
        
        # 저장소별 분포
        for metadata in self.hybrid_metadata.values():
            storage = metadata.get('storage', 'unknown')
            stats["storage_distribution"][storage] = stats["storage_distribution"].get(storage, 0) + 1
        
        # Unified DB 통계 추가
        if self.unified_adapter.available:
            unified_stats = self.unified_adapter.get_source_statistics()
            stats["unified_stats"] = unified_stats
        
        # Incremental DB 통계 추가
        if self.incremental_manager.available:
            incremental_stats = self.incremental_manager.get_statistics()
            stats["incremental_stats"] = incremental_stats
        
        return stats
    
    def get_update_status(self) -> Dict[str, Any]:
        """업데이트 상태 반환"""
        status = {}
        
        # 소스별 통계
        for doc_id, metadata in self.hybrid_metadata.items():
            source = metadata.get('source', 'unknown')
            storage = metadata.get('storage', 'unknown')
            
            if source not in status:
                status[source] = {
                    'document_count': 0,
                    'last_updated': None,
                    'storage_distribution': {},
                    'documents': []
                }
            
            status[source]['document_count'] += 1
            status[source]['storage_distribution'][storage] = (
                status[source]['storage_distribution'].get(storage, 0) + 1
            )
            
            status[source]['documents'].append({
                'id': doc_id,
                'title': metadata.get('title', 'Unknown'),
                'last_updated': metadata.get('last_updated'),
                'storage': storage
            })
            
            # 최신 업데이트 시간 추적
            last_updated = metadata.get('last_updated')
            if last_updated and (not status[source]['last_updated'] or 
                                last_updated > status[source]['last_updated']):
                status[source]['last_updated'] = last_updated
        
        return status
    
    def metadata_search(self, filter_dict: Dict[str, Any], top_k: int = 10) -> List[Dict[str, Any]]:
        """메타데이터 기반 검색 (키워드 검색용)"""
        try:
            results = []
            
            # 하이브리드 메타데이터에서 검색
            for doc_id, metadata in self.hybrid_metadata.items():
                if self._matches_filter(metadata, filter_dict):
                    # 문서 내용 가져오기
                    content = self._get_document_content(doc_id, metadata)
                    if content:
                        results.append({
                            'id': doc_id,
                            'content': content,
                            'metadata': metadata
                        })
                        
                        if len(results) >= top_k:
                            break
            
            return results
            
        except Exception as e:
            print(f"❌ 메타데이터 검색 오류: {e}")
            return []
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """필터 조건 매칭 확인"""
        try:
            for key, condition in filter_dict.items():
                if key == "$or":
                    # OR 조건 처리
                    if not any(self._matches_filter(metadata, sub_condition) for sub_condition in condition):
                        return False
                elif key in metadata:
                    value = metadata[key]
                    if isinstance(condition, dict):
                        for op, op_value in condition.items():
                            if op == "$contains":
                                if isinstance(value, str) and isinstance(op_value, str):
                                    if op_value.lower() not in value.lower():
                                        return False
                                else:
                                    return False
                            else:
                                return False
                    else:
                        if value != condition:
                            return False
                else:
                    return False
            return True
        except Exception:
            return False
    
    def _get_document_content(self, doc_id: str, metadata: Dict[str, Any]) -> Optional[str]:
        """문서 내용 가져오기"""
        try:
            storage = metadata.get('storage', 'unified')
            
            if storage == 'unified' and self.unified_adapter.available:
                # Unified DB에서 내용 가져오기
                return self.unified_adapter.get_document_content(doc_id)
            elif storage == 'incremental' and self.incremental_manager.available:
                # Incremental DB에서 내용 가져오기
                return self.incremental_manager.get_document_content(doc_id)
            else:
                return metadata.get('content', '')
                
        except Exception as e:
            print(f"⚠️ 문서 내용 가져오기 실패 (doc_id={doc_id}): {e}")
            return metadata.get('content', '')