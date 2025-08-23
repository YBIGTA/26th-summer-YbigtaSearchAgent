# migrate_faiss_to_chroma.py
# -*- coding: utf-8 -*-

import os
import json
import math
import argparse
from typing import Any, Dict, List

import faiss
from chromadb import PersistentClient
from langchain_community.vectorstores import FAISS as LCFAISS
from langchain_core.embeddings import Embeddings


class _NoopEmbeddings(Embeddings):
    """load_local용 더미 임베딩 (실제 임베딩 재계산 안 함)"""
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise RuntimeError("이 스크립트에서는 임베딩을 계산하지 않습니다.")
    def embed_query(self, text: str) -> List[float]:
        raise RuntimeError("이 스크립트에서는 임베딩을 계산하지 않습니다.")


def _scrub_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Chroma가 JSON-serializable만 받으므로, 비직렬화 필드는 str로 변환"""
    out = {}
    for k, v in (meta or {}).items():
        try:
            json.dumps(v)
            out[k] = v
        except Exception:
            out[k] = str(v)
    return out


def main():
    parser = argparse.ArgumentParser(description="FAISS(VectorStore) → ChromaDB 마이그레이션")
    parser.add_argument("--faiss_dir", required=True, help="LC FAISS가 저장된 디렉터리 (예: notion_faiss_index)")
    parser.add_argument("--chroma_dir", required=True, help="Chroma persist 디렉터리")
    parser.add_argument("--collection", required=True, help="Chroma 컬렉션 이름")
    parser.add_argument("--batch", type=int, default=1024, help="추가(add) 배치 크기")
    parser.add_argument("--space", choices=["cosine", "l2", "ip"], default="cosine",
                        help="Chroma HNSW distance space (기본: cosine)")
    parser.add_argument("--normalize", action="store_true",
                        help="코사인 유사도(space=cosine) 사용 시 벡터를 L2 정규화하여 삽입")
    args = parser.parse_args()

    # 1) LC FAISS 열기 (임베딩 재계산 없음)
    print(f"📦 FAISS 불러오는 중: {args.faiss_dir}")
    vs: LCFAISS = LCFAISS.load_local(
        args.faiss_dir, _NoopEmbeddings(), allow_dangerous_deserialization=True
    )

    faiss_index = vs.index
    mapping = vs.index_to_docstore_id     # { int_index -> doc_id(str) }
    docstore = vs.docstore                # 문서 저장소

    if not hasattr(faiss_index, "reconstruct"):
        raise RuntimeError(
            "이 FAISS 인덱스는 reconstruct를 지원하지 않습니다.\n"
            "- 보통 LangChain FAISS 기본은 IndexFlatL2라 reconstruct 가능해야 합니다.\n"
            "- IVF/PQ 등으로 만들었다면, 원본 벡터 없이 정확 복원이 어려울 수 있어요.\n"
            "  (가능하면 IndexFlat 기반으로 다시 빌드하거나, 임베딩을 따로 보관했다가 사용하세요.)"
        )

    # 2) Chroma 클라이언트/컬렉션 준비
    print(f"💾 ChromaDB 초기화: {args.chroma_dir} (collection: {args.collection}, space: {args.space})")
    client = PersistentClient(path=args.chroma_dir)
    # 거리함수는 컬렉션 메타데이터의 hnsw:space로 지정
    coll = client.get_or_create_collection(
        name=args.collection,
        metadata={"hnsw:space": args.space}
    )

    # 3) FAISS → Chroma 이식
    positions = sorted(mapping.keys())  # 인덱스 포지션 정렬
    total = len(positions)
    print(f"🚚 이전할 벡터/문서 개수: {total}")

    def l2_normalize(vec: List[float]) -> List[float]:
        if not args.normalize:
            return vec
        import numpy as np
        v = np.array(vec, dtype="float32")
        n = np.linalg.norm(v)
        return (v / (n + 1e-12)).tolist()

    # 배치 추가
    for start in range(0, total, args.batch):
        end = min(start + args.batch, total)
        batch_pos = positions[start:end]

        ids: List[str] = []
        docs: List[str] = []
        metas: List[Dict[str, Any]] = []
        embs: List[List[float]] = []

        for pos in batch_pos:
            doc_id = mapping[pos]
            doc = docstore.search(doc_id)  # langchain.schema.Document
            text = doc.page_content if hasattr(doc, "page_content") else str(doc)
            meta = _scrub_metadata(getattr(doc, "metadata", {}) or {})

            vec = faiss_index.reconstruct(pos)  # numpy array(float32)
            vec_list = [float(x) for x in vec]  # to Python list
            vec_list = l2_normalize(vec_list)

            ids.append(str(doc_id))
            docs.append(text)
            metas.append(meta)
            embs.append(vec_list)

        print(f"  ➕ {start:,} ~ {end-1:,} 추가 중...")
        coll.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)

    # 4) 디스크에 저장
    print("🎉 마이그레이션 완료! →", os.path.abspath(args.chroma_dir))

    # 5) 간단 검증
    print(f"✅ 컬렉션 '{args.collection}' 문서 수 (추정): {coll.count()}")
    print("   이제 Chroma 기반으로 검색/서빙 코드를 교체하면 됩니다.")


if __name__ == "__main__":
    main()


# python f2c.py --faiss_dir notion_faiss_index --normalize

'''
python f2c.py \
  --chroma-dir ./chroma_all \
  --collection-name all \
  --gdrive-faiss-dir ./gdrive_faiss_index \
  --notion-faiss-dir ./notion_faiss_index \
  --github-faiss-dir ./github_faiss_index \
'''