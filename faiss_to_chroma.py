# python faiss_to_chroma.py {faiss_path} 

import os
import shutil
import uuid
import argparse
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from openai import OpenAI
from typing import List
import chromadb

# --- 설정 (Configuration) ---
load_dotenv()
CHROMA_DB_PATH = "unified_chroma_db"  # 모든 데이터를 저장할 통합 DB 경로
DEFAULT_COLLECTION_NAME = "unified_knowledge_db" # 모든 데이터를 저장할 단일 컬렉션 이름

# --- 맞춤 임베딩 클래스 (이전과 동일) ---
class CustomUpstageEmbeddings(Embeddings):
    def __init__(self, model: str = "embedding-passage"):
        self.model = model
        api_key = os.getenv("UPSTAGE_API_KEY")
        if not api_key:
            raise ValueError(".env 파일에 UPSTAGE_API_KEY가 설정되지 않았습니다.")
        self.client = OpenAI(api_key=api_key, base_url="https://api.upstage.ai/v1")

    def _embed(self, texts: List[str], model: str) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(input=texts, model=model)
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"🚨 Upstage API 요청 중 오류 발생: {e}")
            zero_vector = [0.0] * 768
            return [zero_vector] * len(texts)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts, model=self.model)

    def embed_query(self, text: str) -> List[float]:
        query_model = self.model.replace("passage", "query") if "passage" in self.model else self.model
        return self._embed([text], model=query_model)[0]

# --- 메인 로직 ---
def merge_faiss_to_chroma(faiss_path: str, collection_name: str):
    """FAISS 인덱스를 기존 ChromaDB 컬렉션에 추가(병합)합니다."""
    print("="*50)
    print(f"FAISS '{faiss_path}' to ChromaDB 컬렉션 '{collection_name}' 병합을 시작합니다.")

    if not os.path.exists(faiss_path):
        print(f"🚨 오류: '{faiss_path}' 경로에 FAISS 인덱스가 없습니다.")
        return

    print(f"🔄 '{faiss_path}'에서 FAISS 인덱스를 로드합니다...")
    try:
        embeddings = CustomUpstageEmbeddings()
        faiss_vectorstore = FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)
        print("✅ FAISS 인덱스 로드 완료.")
    except Exception as e:
        print(f"🚨 FAISS 인덱스 로드 중 오류 발생: {e}")
        return

    print(f"🔄 ChromaDB를 '{CHROMA_DB_PATH}' 경로에서 로드하거나 새로 생성합니다...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    # ✅ 컬렉션이 없으면 새로 만들고, 있으면 기존 컬렉션을 불러옵니다.
    collection = chroma_client.get_or_create_collection(name=collection_name)
    print(f"✅ ChromaDB 컬렉션 '{collection_name}' 준비 완료. (현재 문서 수: {collection.count()})")

    print("🔄 FAISS에서 문서와 벡터 데이터를 추출합니다...")
    try:
        docstore = faiss_vectorstore.docstore
        index_to_docstore_id = faiss_vectorstore.index_to_docstore_id
        documents, metadatas, ids, embeddings_list = [], [], [], []
        total_vectors = faiss_vectorstore.index.ntotal
        all_vectors = faiss_vectorstore.index.reconstruct_n(0, total_vectors)

        for i in range(total_vectors):
            docstore_id = index_to_docstore_id.get(i)
            if docstore_id is None: continue
            doc = docstore.search(docstore_id)
            if doc is None: continue
            
            documents.append(doc.page_content)
            metadatas.append(doc.metadata)
            ids.append(str(uuid.uuid4()))
            embeddings_list.append(all_vectors[i].tolist())

        print(f"✅ 총 {len(documents)}개의 문서를 FAISS에서 성공적으로 추출했습니다.")
    except Exception as e:
        print(f"🚨 FAISS에서 데이터 추출 중 오류 발생: {e}")
        return

    print(f"🔄 ChromaDB에 {len(documents)}개의 새 문서를 추가합니다...")
    try:
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            collection.add(
                embeddings=embeddings_list[i:i + batch_size],
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
                ids=ids[i:i + batch_size]
            )
            print(f"  - {min(i + batch_size, len(documents))} / {len(documents)} 개 문서 추가 완료...")
        
        print("✅ ChromaDB에 모든 문서 추가 완료.")
        print(f"📊 최종 컬렉션 문서 수: {collection.count()}")
    except Exception as e:
        print(f"🚨 ChromaDB에 데이터 추가 중 오류 발생: {e}")
        return

    print("="*50)
    print(f"🎉 '{faiss_path}'의 데이터를 '{collection_name}' 컬렉션에 성공적으로 병합했습니다!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="여러 FAISS 인덱스를 하나의 ChromaDB 컬렉션으로 병합하는 스크립트")
    parser.add_argument("faiss_path", type=str, help="병합할 FAISS 인덱스 폴더 경로")
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION_NAME, 
                        help=f"데이터를 저장할 ChromaDB 컬렉션 이름 (기본값: {DEFAULT_COLLECTION_NAME})")
    args = parser.parse_args()
    
    merge_faiss_to_chroma(args.faiss_path, args.collection)