# migrate_faiss_to_chroma.py
# -*- coding: utf-8 -*-
"""
FAISS(VectorStore, LangChain 저장형식) -> ChromaDB 마이그레이션 스크립트
- 임베딩 재계산 없이 FAISS에서 벡터를 추출하여 그대로 Chroma에 적재
- 문서(document)와 메타데이터(metadata)도 함께 이전
- gdrive, notion, github 세 개의 FAISS 인덱스를 통합
"""

import os
import json
import argparse
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import faiss
from chromadb import Client
from chromadb.config import Settings
from langchain_community.vectorstores import FAISS as LCFAISS
from langchain.schema import Document


def load_langchain_faiss(faiss_dir: str) -> LCFAISS:
    if not os.path.isdir(faiss_dir):
        raise FileNotFoundError(f"FAISS 디렉터리를 찾을 수 없습니다: {faiss_dir}")
    # embeddings 인스턴스는 로드 시 필요없고, 재직렬화 허용 플래그만 지정
    # (문서/메타데이터와 faiss index만 읽어옴)
    vec = LCFAISS.load_local(
        folder_path=faiss_dir,
        embeddings=None,
        allow_dangerous_deserialization=True,
    )
    return vec


def extract_all_doc_ids(vec: LCFAISS) -> List[str]:
    # LangChain FAISS 구조:
    # - vec.index_to_docstore_id: List[int->str] 또는 Dict[int->str] 형태
    # - vec.docstore._dict: {doc_id(str): Document}
    mapping = vec.index_to_docstore_id
    if isinstance(mapping, dict):
        # 일부 버전에선 dict일 수 있음 (key: int index, value: doc_id)
        ordered = [mapping[i] for i in sorted(mapping.keys())]
        return ordered
    elif isinstance(mapping, list):
        return list(mapping)
    else:
        raise TypeError(f"지원하지 않는 index_to_docstore_id 타입: {type(mapping)}")


def get_documents_and_metadatas(vec: LCFAISS, doc_ids: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
    texts: List[str] = []
    metas: List[Dict[str, Any]] = []
    # vec.docstore._dict 에서 Document를 꺼냄
    store: Dict[str, Document] = getattr(vec.docstore, "_dict", {})
    for doc_id in doc_ids:
        doc: Optional[Document] = store.get(doc_id)
        if doc is None:
            # 드물게 누락돼 있을 수 있음
            texts.append("")
            metas.append({"_warning": "document_missing"})
        else:
            texts.append(doc.page_content or "")
            # metadata가 dict가 아닐 수도 있으므로 방어적 캐스팅
            md = dict(doc.metadata) if isinstance(doc.metadata, dict) else {}
            metas.append(md)
    return texts, metas


def faiss_reconstruct_all(index: faiss.Index, expected_dim: Optional[int] = None) -> np.ndarray:
    """FAISS 인덱스에 저장된 모든 벡터를 추출.
    - IndexFlat* 계열: reconstruct_n 또는 xb 노출
    - IVF 등: reconstruct/reconstruct_n 지원 시 사용 (지원 안되면 실패 가능)
    """
    n = index.ntotal
    if n == 0:
        return np.empty((0, expected_dim or 0), dtype="float32")

    # 시도 1) reconstruct_n
    if hasattr(index, "reconstruct_n"):
        try:
            arr = np.zeros((n, index.d), dtype="float32")
            index.reconstruct_n(0, n, faiss.swig_ptr(arr))
            if expected_dim is not None and arr.shape[1] != expected_dim:
                raise ValueError(f"차원 불일치: FAISS={arr.shape[1]}, 기대값={expected_dim}")
            return arr
        except Exception:
            pass

    # 시도 2) IndexFlat 계열의 xb 추출
    # 일부 SWIG 바인딩에서 index.xb 접근 가능
    if hasattr(index, "xb"):
        try:
            xb = faiss.vector_to_array(index.xb)
            arr = xb.reshape(n, index.d).astype("float32")
            if expected_dim is not None and arr.shape[1] != expected_dim:
                raise ValueError(f"차원 불일치: FAISS={arr.shape[1]}, 기대값={expected_dim}")
            return arr
        except Exception:
            pass

    # 시도 3) 한 개씩 reconstruct
    if hasattr(index, "reconstruct"):
        try:
            arr = np.zeros((n, index.d), dtype="float32")
            for i in range(n):
                v = np.zeros((index.d,), dtype="float32")
                index.reconstruct(i, faiss.swig_ptr(v))
                arr[i] = v
            if expected_dim is not None and arr.shape[1] != expected_dim:
                raise ValueError(f"차원 불일치: FAISS={arr.shape[1]}, 기대값={expected_dim}")
            return arr
        except Exception:
            pass

    raise RuntimeError(
        "이 FAISS 인덱스 타입에서는 벡터를 재구성(reconstruct)할 수 없습니다.\n"
        "- IndexIVF/PQ 계열은 원본 벡터를 저장하지 않을 수 있습니다.\n"
        "- 이 경우, 임베딩을 보유한 원천에서 재계산 후 Chroma에 적재해야 합니다."
    )


def chunked(iterable, size: int):
    buf = []
    for x in iterable:
        buf.append(x)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf


def process_faiss_index(faiss_dir: str, source_name: str, expected_dim: int) -> Tuple[List[str], List[str], List[Dict[str, Any]], np.ndarray]:
    """단일 FAISS 인덱스를 처리하여 문서와 벡터를 추출"""
    print(f"🔹 {source_name} FAISS 로드 중... ({faiss_dir})")
    vec = load_langchain_faiss(faiss_dir)
    
    # 문서 ID, 텍스트/메타데이터
    print(f"🔹 {source_name} 문서/메타데이터 적재 중...")
    doc_ids = extract_all_doc_ids(vec)
    texts, metas = get_documents_and_metadatas(vec, doc_ids)
    
    # 소스 정보를 메타데이터에 추가
    for meta in metas:
        meta["source_type"] = source_name
    
    # 벡터 추출
    print(f"🔹 {source_name} FAISS 인덱스에서 임베딩 추출 중...")
    index: faiss.Index = vec.index
    emb = faiss_reconstruct_all(index, expected_dim=expected_dim)
    
    n_total = emb.shape[0]
    if n_total != len(doc_ids):
        raise ValueError(f"{source_name}: 벡터 수({n_total})와 문서 수({len(doc_ids)})가 다릅니다.")
    
    print(f"✅ {source_name}: {n_total}개 벡터 추출 완료")
    return doc_ids, texts, metas, emb


def main():
    parser = argparse.ArgumentParser(description="FAISS(4096차원) -> ChromaDB 마이그레이션 - 통합 버전")
    parser.add_argument("--chroma-dir", required=True, help="ChromaDB persist 디렉터리 경로")
    parser.add_argument("--collection-name", required=True, help="생성/타겟 컬렉션 이름")
    parser.add_argument("--batch-size", type=int, default=1000, help="Chroma add 배치 크기 (기본 1000)")
    parser.add_argument("--expected-dim", type=int, default=4096, help="임베딩 차원 검증 (기본 4096)")
    parser.add_argument("--gdrive-faiss-dir", default="gdrive_faiss_index", help="Google Drive FAISS 디렉터리 경로")
    parser.add_argument("--notion-faiss-dir", default="notion_faiss_index", help="Notion FAISS 디렉터리 경로")
    parser.add_argument("--github-faiss-dir", default="github_faiss_index", help="GitHub FAISS 디렉터리 경로")
    args = parser.parse_args()

    # FAISS 인덱스 디렉터리들
    faiss_dirs = {
        "gdrive": args.gdrive_faiss_dir,
        "notion": args.notion_faiss_dir,
        "github": args.github_faiss_dir
    }

    # 모든 FAISS 인덱스에서 데이터 추출
    all_doc_ids = []
    all_texts = []
    all_metas = []
    all_embeddings = []
    
    total_vectors = 0
    
    for source_name, faiss_dir in faiss_dirs.items():
        if os.path.isdir(faiss_dir):
            try:
                doc_ids, texts, metas, emb = process_faiss_index(faiss_dir, source_name, args.expected_dim)
                
                # 고유한 ID 생성 (소스별 prefix 추가)
                prefixed_doc_ids = [f"{source_name}_{doc_id}" for doc_id in doc_ids]
                
                all_doc_ids.extend(prefixed_doc_ids)
                all_texts.extend(texts)
                all_metas.extend(metas)
                all_embeddings.append(emb)
                
                total_vectors += len(doc_ids)
                print(f"✅ {source_name}: {len(doc_ids)}개 벡터 처리 완료")
                
            except Exception as e:
                print(f"⚠️ {source_name} 처리 중 오류 발생: {e}")
                continue
        else:
            print(f"⚠️ {source_name} FAISS 디렉터리를 찾을 수 없습니다: {faiss_dir}")

    if total_vectors == 0:
        raise ValueError("처리할 수 있는 FAISS 인덱스가 없습니다.")

    # 모든 임베딩을 하나로 합치기
    print("🔹 모든 임베딩 통합 중...")
    combined_embeddings = np.vstack(all_embeddings)
    print(f"✅ 총 {total_vectors}개 벡터 통합 완료")

    # Chroma 클라이언트/컬렉션 준비
    print("🔹 ChromaDB 초기화 중...")
    client = Client(
        Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=args.chroma_dir,
        )
    )

    # 기존 컬렉션이 있으면 가져오고, 없으면 생성
    try:
        collection = client.get_collection(args.collection_name)
        print(f"✅ 기존 컬렉션 사용: {args.collection_name}")
    except Exception:
        collection = client.create_collection(
            name=args.collection_name,
            metadata={"source": "faiss_migration", "dim": args.expected_dim, "sources": list(faiss_dirs.keys())},
            embedding_function=None,  # 직접 embeddings 공급
        )
        print(f"✅ 새 컬렉션 생성: {args.collection_name}")

    print(f"🔹 총 {total_vectors}개 벡터를 배치({args.batch_size})로 업로드합니다...")
    
    # 안정적인 id 문자열 구성
    def make_id(i: int, doc_id: str) -> str:
        return doc_id if (doc_id and isinstance(doc_id, str)) else f"combined_{i}"

    # 업로드
    uploaded = 0
    for batch_indices in chunked(range(total_vectors), args.batch_size):
        ids = [make_id(i, all_doc_ids[i]) for i in batch_indices]
        batch_embeddings = combined_embeddings[batch_indices].astype("float32")
        batch_texts = [all_texts[i] for i in batch_indices]
        batch_metas = [all_metas[i] for i in batch_indices]

        # Chroma add: documents/embeddings/metadatas/ids 길이는 동일해야 함
        collection.add(
            ids=ids,
            embeddings=batch_embeddings.tolist(),  # list of list[float]
            documents=batch_texts,
            metadatas=batch_metas,
        )
        uploaded += len(batch_indices)
        print(f"  - 누적 업로드: {uploaded}/{total_vectors}")

    # Persist 저장
    client.persist()
    print("🎉 마이그레이션 완료!")
    print(f"- To Chroma: {args.chroma_dir} (collection='{args.collection_name}')")
    print(f"- 총 업로드: {uploaded} vectors")
    print(f"- 처리된 소스: {list(faiss_dirs.keys())}")


if __name__ == "__main__":
    main()

'''
아래 코드로 실행
python migrate_faiss_to_chroma.py \
  --chroma-dir ./chroma_store \
  --collection-name my_collection \
  --gdrive-faiss-dir ./gdrive_faiss_index \
  --notion-faiss-dir ./notion_faiss_index \
  --github-faiss-dir ./github_faiss_index
'''