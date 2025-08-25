# read_chromadb_direct.py
import chromadb
from chromadb.config import Settings
import os

def read_chromadb_direct():
    """ChromaDB 파일에서 직접 데이터를 읽어서 보여줍니다."""
    
    chroma_path = "data/indexes/chroma_db"
    
    if not os.path.exists(chroma_path):
        print(f"❌ ChromaDB 경로가 없습니다: {chroma_path}")
        return
    
    try:
        # ChromaDB 클라이언트 초기화
        client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        print(f"🔍 ChromaDB 직접 읽기")
        print(f"=" * 50)
        
        # 모든 컬렉션 목록 확인
        collections = client.list_collections()
        print(f"📋 ChromaDB 컬렉션 목록:")
        
        if not collections:
            print("  - 컬렉션이 없습니다.")
            return
        
        for collection in collections:
            print(f"  - {collection.name}: {collection.count()}개 문서")
            
            # 각 컬렉션의 데이터 읽기
            try:
                # 컬렉션에서 모든 데이터 가져오기
                results = collection.get(
                    include=['metadatas', 'documents', 'embeddings']
                )
                
                if results['ids']:
                    print(f"    📊 문서 통계:")
                    print(f"      - 총 문서 수: {len(results['ids'])}개")
                    
                    # 소스별 통계
                    source_stats = {}
                    for metadata in results['metadatas']:
                        if metadata:
                            source = metadata.get('source', 'unknown')
                            source_stats[source] = source_stats.get(source, 0) + 1
                    
                    print(f"      - 소스별 분포:")
                    for source, count in source_stats.items():
                        print(f"        • {source}: {count}개")
                    
                    # 처음 10개 문서 보여주기
                    print(f"      - 문서 목록 (처음 10개):")
                    for i in range(min(10, len(results['ids']))):
                        doc_id = results['ids'][i]
                        metadata = results['metadatas'][i] if results['metadatas'] else {}
                        document = results['documents'][i] if results['documents'] else ""
                        
                        title = metadata.get('title', 'Unknown')
                        source = metadata.get('source', 'unknown')
                        last_updated = metadata.get('last_updated', 'Unknown')
                        
                        # 문서 내용 미리보기 (처음 100자)
                        content_preview = document[:100] + "..." if len(document) > 100 else document
                        
                        print(f"        {i+1:2d}. {title} ({source})")
                        print(f"            ID: {doc_id}")
                        print(f"            업데이트: {last_updated}")
                        print(f"            내용: {content_preview}")
                        print()
                    
                    if len(results['ids']) > 10:
                        print(f"        ... 그리고 {len(results['ids']) - 10}개 더")
                    
                    # 전체 문서 목록 보기 옵션
                    show_all = input("전체 문서 목록을 보시겠습니까? (y/n): ").lower()
                    if show_all == 'y':
                        print(f"\n📋 전체 문서 목록:")
                        for i in range(len(results['ids'])):
                            doc_id = results['ids'][i]
                            metadata = results['metadatas'][i] if results['metadatas'] else {}
                            title = metadata.get('title', 'Unknown')
                            source = metadata.get('source', 'unknown')
                            last_updated = metadata.get('last_updated', 'Unknown')
                            print(f"  {i+1:3d}. {title} ({source}) - {last_updated}")
                
                else:
                    print(f"    📭 컬렉션에 문서가 없습니다.")
                    
            except Exception as e:
                print(f"    ❌ 컬렉션 읽기 오류: {e}")
        
        # ChromaDB 파일 정보
        print(f"\n�� ChromaDB 파일 정보:")
        sqlite_file = os.path.join(chroma_path, "chroma.sqlite3")
        if os.path.exists(sqlite_file):
            size = os.path.getsize(sqlite_file)
            print(f"  - chroma.sqlite3: {size / (1024*1024):.1f} MB")
        
        # 임베딩 폴더들
        embedding_dirs = [d for d in os.listdir(chroma_path) 
                         if os.path.isdir(os.path.join(chroma_path, d)) 
                         and len(d) == 36]  # UUID 형식
        
        print(f"  - 임베딩 폴더: {len(embedding_dirs)}개")
        for i, folder in enumerate(embedding_dirs[:5]):  # 처음 5개만
            folder_path = os.path.join(chroma_path, folder)
            size = sum(os.path.getsize(os.path.join(folder_path, f)) 
                      for f in os.listdir(folder_path) 
                      if os.path.isfile(os.path.join(folder_path, f)))
            print(f"    • {folder}: {size / 1024:.1f} KB")
        
        if len(embedding_dirs) > 5:
            print(f"    • ... 그리고 {len(embedding_dirs) - 5}개 더")
        
    except Exception as e:
        print(f"❌ ChromaDB 읽기 오류: {e}")

if __name__ == "__main__":
    read_chromadb_direct()