"""
UnifiedChromaAdapter - unified_chroma_db 호환성 어댑터

기존 unified_chroma_db의 데이터 구조를 현재 시스템과 호환되도록 
변환하는 어댑터 패턴을 구현합니다.

- ChromaDB 메타데이터를 직접 수정하지 않음
- 런타임에 호환성 레이어 제공  
- 기존 데이터 무손실 보장
"""

import os
import hashlib
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None
    Settings = None
    CHROMADB_AVAILABLE = False

from langchain_core.documents import Document


class UnifiedChromaAdapter:
    """unified_chroma_db와 현재 시스템 간의 호환성 어댑터"""
    
    def __init__(self, unified_db_path: str = "data/unified_chroma_db/unified_chroma_db"):
        self.unified_db_path = unified_db_path
        self.available = CHROMADB_AVAILABLE and os.path.exists(unified_db_path)
        
        if not self.available:
            print(f"⚠️ Unified ChromaDB를 찾을 수 없습니다: {unified_db_path}")
            return
            
        # 가상 메타데이터 저장소 (document_metadata.json 호환)
        self.virtual_metadata = {}
        
        # ChromaDB 클라이언트 초기화
        try:
            self.client = chromadb.PersistentClient(
                path=unified_db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False  # 읽기 전용
                )
            )
            self.collection = self._get_unified_collection()
            
            # 초기화 시 가상 메타데이터 생성
            self._generate_virtual_metadata()
            
        except Exception as e:
            print(f"❌ Unified ChromaDB 초기화 실패: {e}")
            self.available = False
    
    def _get_unified_collection(self):
        """unified_chroma_db의 컬렉션을 가져옵니다."""
        collections = self.client.list_collections()
        if not collections:
            print("❌ unified_chroma_db에 컬렉션이 없습니다.")
            return None
            
        # 첫 번째 컬렉션 사용 (보통 unified_knowledge_db)
        collection = collections[0]
        print(f"✅ Unified 컬렉션 로드: {collection.name}")
        return collection
    
    def generate_doc_id_from_source(self, source: str) -> str:
        """unified_db의 source를 현재 시스템 doc_id 형식으로 변환"""
        if source.startswith('https://github.com/YBIGTA/'):
            repo_name = source.split('/')[-1]
            return f"github:github_{repo_name}"
        elif source.startswith('notion_page_'):
            page_id = source.replace('notion_page_', '')
            return f"notion:{page_id}"
        elif source.endswith('.pdf') or source.endswith('.docx') or source.endswith('.xlsx'):
            return source  # 파일은 그대로 사용
        else:
            # 기타 소스는 해시 기반 ID 생성
            return f"unified:{hashlib.md5(source.encode()).hexdigest()[:8]}"
    
    def _generate_virtual_metadata(self):
        """기존 ChromaDB 데이터에서 가상 메타데이터 생성"""
        if not self.collection:
            return
            
        print("🔄 가상 document_metadata 생성 중...")
        
        try:
            # SQLite에서 직접 메타데이터 조회 (더 효율적)
            sqlite_path = os.path.join(self.unified_db_path, "chroma.sqlite3")
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            
            # 소스별로 그룹핑된 데이터 조회
            cursor.execute('''
                SELECT 
                    em_source.string_value as source,
                    em_title.string_value as title,
                    e.created_at,
                    GROUP_CONCAT(e.embedding_id) as embedding_ids,
                    COUNT(*) as chunk_count
                FROM embeddings e
                JOIN embedding_metadata em_source ON e.id = em_source.id AND em_source.key = 'source'
                LEFT JOIN embedding_metadata em_title ON e.id = em_title.id AND em_title.key = 'title'
                GROUP BY em_source.string_value, em_title.string_value
                ORDER BY e.created_at DESC
            ''')
            
            source_groups = cursor.fetchall()
            
            for source_data in source_groups:
                source, title, created_at, embedding_ids, chunk_count = source_data
                
                # doc_id 생성
                doc_id = self.generate_doc_id_from_source(source)
                
                # 컨텐츠 해시 생성 (소스 기반)
                content_hash = hashlib.sha256(f"{source}:{title}:{chunk_count}".encode()).hexdigest()
                
                # 가상 메타데이터 저장
                self.virtual_metadata[doc_id] = {
                    'content_hash': content_hash,
                    'last_updated': created_at or datetime.now().isoformat(),
                    'source': self._normalize_source_type(source),
                    'title': title or 'Unknown',
                    'chunk_count': chunk_count,
                    'original_source': source  # 원본 소스 보존
                }
            
            conn.close()
            print(f"✅ {len(self.virtual_metadata)}개 문서의 가상 메타데이터 생성 완료")
            
        except Exception as e:
            print(f"❌ 가상 메타데이터 생성 실패: {e}")
    
    def _normalize_source_type(self, source: str) -> str:
        """소스를 표준 타입으로 정규화"""
        if source.startswith('https://github.com/'):
            return 'github'
        elif source.startswith('notion_page_'):
            return 'notion'
        elif any(source.endswith(ext) for ext in ['.pdf', '.docx', '.xlsx', '.pptx']):
            return 'file'
        else:
            return 'unknown'
    
    def get_virtual_metadata(self) -> Dict[str, Dict[str, Any]]:
        """현재 시스템 호환 형식의 가상 메타데이터 반환"""
        return self.virtual_metadata.copy()
    
    def save_virtual_metadata_to_file(self, file_path: str):
        """가상 메타데이터를 파일로 저장 (호환성 확인용)"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.virtual_metadata, f, ensure_ascii=False, indent=2)
        print(f"📄 가상 메타데이터 저장: {file_path}")
    
    def get_documents_by_source(self, source_type: str) -> List[str]:
        """특정 소스 타입의 문서 목록 반환"""
        return [
            doc_id for doc_id, metadata in self.virtual_metadata.items()
            if metadata.get('source') == source_type
        ]
    
    def check_document_exists(self, doc_id: str) -> bool:
        """문서가 unified_db에 존재하는지 확인"""
        return doc_id in self.virtual_metadata
    
    def get_source_statistics(self) -> Dict[str, Any]:
        """소스별 통계 반환"""
        stats = {}
        for doc_id, metadata in self.virtual_metadata.items():
            source_type = metadata.get('source', 'unknown')
            if source_type not in stats:
                stats[source_type] = {
                    'document_count': 0,
                    'total_chunks': 0,
                    'last_updated': None
                }
            
            stats[source_type]['document_count'] += 1
            stats[source_type]['total_chunks'] += metadata.get('chunk_count', 0)
            
            last_updated = metadata.get('last_updated')
            if last_updated and (not stats[source_type]['last_updated'] or 
                                last_updated > stats[source_type]['last_updated']):
                stats[source_type]['last_updated'] = last_updated
        
        return stats
    
    def search_documents(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """unified_db에서 문서 검색 (ChromaDB 검색 래핑)"""
        if not self.collection:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0.0
                    
                    # 가상 doc_id 생성
                    original_source = metadata.get('source', 'unknown')
                    virtual_doc_id = self.generate_doc_id_from_source(original_source)
                    
                    formatted_results.append({
                        'document': Document(page_content=doc, metadata=metadata),
                        'score': 1.0 - distance,  # 거리를 점수로 변환
                        'content': doc,
                        'metadata': {**metadata, 'doc_id': virtual_doc_id},
                        'type': 'vector_unified'
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Unified DB 검색 실패: {e}")
            return []