# migrate_faiss_to_chroma_multi.py
# -*- coding: utf-8 -*-

import os
import json
import argparse
from typing import Any, Dict, List, Tuple

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


def _l2_normalize(vec: List[float], do_norm: bool) -> List[float]:
    if not do_norm:
        return vec
    import numpy as np
    v = np.array(vec, dtype="float32")
    n = float(np.linalg.norm(v))
    return (v / (n + 1e-12)).tolist()


def _load_faiss_as_iter(
    faiss_dir: str,
    label: str,
    normalize: bool,
) -> Tuple[int, Any]:
    """
    주어진 LC-FAISS 디렉터리를 열고, (pos -> item dict) 를 배치로 뽑아낼 수 있도록
    제너레이터를 반환.
    """
    print(f"📦 FAISS 불러오는 중: {faiss_dir} (label={label})")
    vs: LCFAISS = LCFAISS.load_local(
        faiss_dir, _NoopEmbeddings(), allow_dangerous_deserialization=True
    )
    faiss_index = vs.index
    mapping = vs.index_to_docstore_id     # { int_index -> doc_id(str) }
    docstore = vs.docstore                # 문서 저장소

    if not hasattr(faiss_index, "reconstruct"):
        raise RuntimeError(
            f"[{faiss_dir}] 이 FAISS 인덱스는 reconstruct를 지원하지 않습니다.\n"
            "- 보통 LangChain FAISS 기본은 IndexFlatL2라 reconstruct 가능해야 합니다.\n"
            "- IVF/PQ 등으로 만들었다면, 원본 벡터 없이 정확 복원이 어려울 수 있어요.\n"
            "  (가능하면 IndexFlat 기반으로 다시 빌드하거나, 임베딩을 따로 보관했다가 사용하세요.)"
        )

    positions = sorted(mapping.keys())
    total = len(positions)

    def iterator(batch_size: int):
        for start in range(0, total, batch_size):
            end = min(start + batch_size, total)
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
                # 출처 라벨 추가
                meta = {**meta, "_source": label}

                vec = faiss_index.reconstruct(pos)  # numpy array(float32)
                vec_list = [float(x) for x in vec]
                vec_list = _l2_normalize(vec_list, normalize)

                # 충돌 방지를 위한 composite id (label:doc_id)
                ids.append(f"{label}:{doc_id}")
                docs.append(text)
                metas.append(meta)
                embs.append(vec_list)
            yield start, end, ids, docs, metas, embs

    return total, iterator


def main():
    parser = argparse.ArgumentParser(description="여러 FAISS(VectorStore) → 단일 ChromaDB 컬렉션 마이그레이션")
    parser.add_argument(
        "--faiss_dirs",
        nargs="+",
        required=True,
        help="LC FAISS 디렉터리 목록 (예: notion_faiss_index gdrive_faiss_index github_faiss_index)",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        default=None,
        help="각 FAISS 디렉터리의 라벨(출처) 목록. 미지정 시 디렉터리 basename 사용",
    )
    parser.add_argument("--chroma_dir", required=True, help="Chroma persist 디렉터리 (단일)")
    parser.add_argument("--collection", required=True, help="Chroma 컬렉션 이름 (단일)")
    parser.add_argument("--batch", type=int, default=1024, help="추가(add) 배치 크기")
    parser.add_argument("--space", choices=["cosine", "l2", "ip"], default="cosine",
                        help="Chroma HNSW distance space (기본: cosine)")
    parser.add_argument("--normalize", action="store_true",
                        help="코사인 유사도(space=cosine) 사용 시 벡터를 L2 정규화하여 삽입")
    args = parser.parse_args()

    # labels 정리
    faiss_dirs: List[str] = args.faiss_dirs
    if args.labels is None:
        labels = [os.path.basename(os.path.normpath(d)) for d in faiss_dirs]
    else:
        if len(args.labels) != len(faiss_dirs):
            raise ValueError("--labels 개수는 --faiss_dirs 개수와 동일해야 합니다.")
        labels = args.labels

    print(f"💾 ChromaDB 초기화: {args.chroma_dir} (collection: {args.collection}, space: {args.space})")
    client = PersistentClient(path=args.chroma_dir)
    coll = client.get_or_create_collection(
        name=args.collection,
        metadata={"hnsw:space": args.space}
    )

    grand_total = 0
    for d in faiss_dirs:
        # 미리 총 개수 파악
        vs_tmp: LCFAISS = LCFAISS.load_local(
            d, _NoopEmbeddings(), allow_dangerous_deserialization=True
        )
        grand_total += len(vs_tmp.index_to_docstore_id)

    print(f"🚚 이전할 전체 벡터/문서 개수 (합): {grand_total:,}")

    # 각 디렉터리 순회하며 동일 컬렉션으로 add
    processed = 0
    for d, label in zip(faiss_dirs, labels):
        total, iterator = _load_faiss_as_iter(d, label, args.normalize)
        print(f"▶ 시작: {d} (총 {total:,}개, label={label})")

        for start, end, ids, docs, metas, embs in iterator(args.batch):
            print(f"  ➕ [{label}] {start:,} ~ {end-1:,} 추가 중...")
            coll.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
            processed += (end - start)

    print("🎉 마이그레이션 완료! →", os.path.abspath(args.chroma_dir))
    print(f"✅ 컬렉션 '{args.collection}' 문서 수 (추정): {coll.count()}")
    print("   이제 Chroma 기반으로 검색/서빙 코드를 교체하면 됩니다.")
    print(f"   (총 삽입 시도 수: {processed:,})")


if __name__ == "__main__":
    main()


'''
python migrate_faiss_to_chroma_multi.py \
  --faiss_dirs gdrive_faiss_index notion_faiss_index github_faiss_index \
  --labels gdrive notion github \
  --chroma_dir ./chroma_all \
  --collection all \
  --space cosine \
  --normalize \
  --batch 1024
'''

# python migrate_faiss_to_chroma_multi.py   --faiss_dirs gdrive_faiss_index notion_faiss_index    --labels gdrive notion   --chroma_dir ./chroma_all --collection all --space cosine --normalize   --batch 1024