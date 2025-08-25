"""
ChromaDB 데이터를 SQLite documents 테이블로 동기화
FTS 검색을 위해 ChromaDB의 문서들을 SQLite로 복사
"""

import os
import sys
import chromadb
from chromadb.config import Settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime

# 백엔드 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.models import init_db, Document

def sync_chroma_to_sqlite():
    """ChromaDB 데이터를 SQLite로 동기화"""
    
    print("🔄 ChromaDB → SQLite 동기화 시작...")
    
    # 1. ChromaDB 연결
    chroma_path = "data/unified_chroma_db/unified_chroma_db"
    if not os.path.exists(chroma_path):
        print(f"❌ ChromaDB 경로를 찾을 수 없습니다: {chroma_path}")
        return False
    
    try:
        client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False, allow_reset=False)
        )
        print("✅ ChromaDB 클라이언트 연결 완료")
    except Exception as e:
        print(f"❌ ChromaDB 연결 실패: {e}")
        return False
    
    # 2. 컬렉션 확인
    collections = client.list_collections()
    if not collections:
        print("❌ ChromaDB에 컬렉션이 없습니다.")
        return False
    
    print(f"📚 발견된 컬렉션: {[col.name for col in collections]}")
    
    # 3. SQLite 연결
    try:
        db_engine = init_db("data/db/app.db")
        SessionLocal = sessionmaker(bind=db_engine)
        session = SessionLocal()
        print("✅ SQLite 연결 완료")
    except Exception as e:
        print(f"❌ SQLite 연결 실패: {e}")
        return False
    
    total_synced = 0
    
    try:
        # 4. 각 컬렉션에서 데이터 추출 및 동기화
        for collection in collections:
            print(f"📖 컬렉션 '{collection.name}' 처리 중...")
            
            # 컬렉션에서 모든 데이터 가져오기
            try:
                results = collection.get(
                    include=['documents', 'metadatas', 'embeddings']
                )
            except Exception as e:
                print(f"⚠️ 컬렉션 '{collection.name}' 데이터 가져오기 실패: {e}")
                continue
            
            if not results['documents']:
                print(f"ℹ️ 컬렉션 '{collection.name}'에 문서가 없습니다.")
                continue
            
            # 5. 각 문서를 SQLite로 복사
            for i, (doc_content, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                try:
                    # 기존 문서 확인 (source와 external_id로)
                    source = metadata.get('source', 'unknown')
                    external_id = metadata.get('source_id', f"{collection.name}_{i}")
                    
                    existing_doc = session.query(Document).filter_by(
                        source=source,
                        external_id=external_id
                    ).first()
                    
                    if existing_doc:
                        # 기존 문서 업데이트
                        existing_doc.title = metadata.get('title', 'Unknown')
                        existing_doc.content = doc_content
                        existing_doc.url = metadata.get('url', '')
                        existing_doc.doc_metadata = metadata
                        existing_doc.updated_at = datetime.now()
                        print(f"  🔄 문서 업데이트: {metadata.get('title', 'Unknown')}")
                    else:
                        # 새 문서 생성
                        new_doc = Document(
                            source=source,
                            external_id=external_id,
                            title=metadata.get('title', 'Unknown'),
                            url=metadata.get('url', ''),
                            content=doc_content,
                            doc_metadata=metadata,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        session.add(new_doc)
                        print(f"  ➕ 새 문서 추가: {metadata.get('title', 'Unknown')}")
                    
                    total_synced += 1
                    
                    # 100개마다 커밋
                    if total_synced % 100 == 0:
                        session.commit()
                        print(f"  💾 중간 저장: {total_synced}개 문서")
                
                except Exception as e:
                    print(f"  ❌ 문서 처리 실패 (인덱스 {i}): {e}")
                    continue
            
            print(f"✅ 컬렉션 '{collection.name}' 완료")
        
        # 6. 최종 커밋
        session.commit()
        print(f"🎉 동기화 완료! 총 {total_synced}개 문서 동기화됨")
        
        # 7. FTS 인덱스 재생성 확인
        print("🔍 FTS 인덱스 상태 확인...")
        fts_count = session.execute(text("SELECT COUNT(*) FROM document_fts")).scalar()
        print(f"📊 FTS 인덱스 문서 수: {fts_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 동기화 중 오류 발생: {e}")
        session.rollback()
        return False
    
    finally:
        session.close()

if __name__ == "__main__":
    success = sync_chroma_to_sqlite()
    if success:
        print("✅ ChromaDB → SQLite 동기화 성공!")
    else:
        print("❌ ChromaDB → SQLite 동기화 실패!")
        sys.exit(1) 