import json
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import numpy as np

class FAISSToElasticsearchConverter:
    def __init__(self, faiss_index_path: str, es_host: str = "localhost", es_port: int = 9200):
        """FAISS 인덱스를 Elasticsearch로 변환하는 클래스"""
        self.faiss_index_path = faiss_index_path
        self.es_client = Elasticsearch([{'host': es_host, 'port': es_port}])
        self.index_name = "notion_documents"
        
    def load_faiss_data(self) -> Dict[str, Any]:
        """FAISS 인덱스에서 데이터를 로드합니다."""
        try:
            # FAISS 인덱스 로드
            vectorstore = FAISS.load_local(self.faiss_index_path, allow_dangerous_deserialization=True)
            
            # 문서와 벡터 추출
            documents = list(vectorstore.docstore._dict.values())
            embeddings = vectorstore.index.reconstruct_n(0, len(documents))
            
            print(f"✅ {len(documents)}개의 문서와 {len(embeddings)}개의 벡터를 로드했습니다.")
            
            return {
                'documents': documents,
                'embeddings': embeddings
            }
            
        except Exception as e:
            print(f"❌ FAISS 데이터 로드 실패: {e}")
            raise
    
    def create_elasticsearch_index(self, mapping: Dict[str, Any] = None):
        """Elasticsearch 인덱스를 생성합니다."""
        if mapping is None:
            # 기본 매핑 설정
            mapping = {
                "mappings": {
                    "properties": {
                        "content": {
                            "type": "text",
                            "analyzer": "standard",
                            "search_analyzer": "standard"
                        },
                        "title": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "source": {
                            "type": "keyword"
                        },
                        "page_id": {
                            "type": "keyword"
                        },
                        "block_count": {
                            "type": "integer"
                        },
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 4096,  # Upstage Solar 임베딩 차원
                            "index": True,
                            "similarity": "cosine"
                        },
                        "created_at": {
                            "type": "date"
                        }
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 100
                    }
                }
            }
        
        try:
            # 기존 인덱스가 있으면 삭제
            if self.es_client.indices.exists(index=self.index_name):
                self.es_client.indices.delete(index=self.index_name)
                print(f"🗑️ 기존 인덱스 '{self.index_name}' 삭제됨")
            
            # 새 인덱스 생성
            self.es_client.indices.create(index=self.index_name, body=mapping)
            print(f"✅ Elasticsearch 인덱스 '{self.index_name}' 생성됨")
            
        except Exception as e:
            print(f"❌ Elasticsearch 인덱스 생성 실패: {e}")
            raise
    
    def convert_to_elasticsearch(self, batch_size: int = 100):
        """FAISS 데이터를 Elasticsearch로 변환합니다."""
        try:
            # FAISS 데이터 로드
            data = self.load_faiss_data()
            documents = data['documents']
            embeddings = data['embeddings']
            
            # Elasticsearch 인덱스 생성
            self.create_elasticsearch_index()
            
            # 배치로 데이터 삽입
            actions = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                action = {
                    "_index": self.index_name,
                    "_id": i,
                    "_source": {
                        "content": doc.page_content,
                        "title": doc.metadata.get("title", "제목 없음"),
                        "source": doc.metadata.get("source", ""),
                        "page_id": doc.metadata.get("page_id", ""),
                        "block_count": doc.metadata.get("block_count", 0),
                        "embedding": embedding.tolist(),
                        "created_at": "2024-01-01T00:00:00Z"  # 기본값
                    }
                }
                actions.append(action)
                
                # 배치 크기에 도달하면 삽입
                if len(actions) >= batch_size:
                    success, failed = bulk(self.es_client, actions, refresh=True)
                    print(f"📦 배치 삽입: 성공 {success}개, 실패 {failed}개")
                    actions = []
            
            # 남은 데이터 삽입
            if actions:
                success, failed = bulk(self.es_client, actions, refresh=True)
                print(f"📦 마지막 배치 삽입: 성공 {success}개, 실패 {failed}개")
            
            print(f"🎉 총 {len(documents)}개의 문서를 Elasticsearch로 변환 완료!")
            
        except Exception as e:
            print(f"❌ Elasticsearch 변환 실패: {e}")
            raise
    
    def search_by_text(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """텍스트 기반 검색을 수행합니다."""
        try:
            response = self.es_client.search(
                index=self.index_name,
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["content^2", "title"],
                            "type": "best_fields",
                            "fuzziness": "AUTO"
                        }
                    },
                    "size": top_k,
                    "_source": ["content", "title", "source", "page_id"]
                }
            )
            
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    'score': hit['_score'],
                    'content': hit['_source']['content'],
                    'title': hit['_source']['title'],
                    'source': hit['_source']['source'],
                    'page_id': hit['_source']['page_id']
                })
            
            return results
            
        except Exception as e:
            print(f"❌ 텍스트 검색 실패: {e}")
            return []
    
    def search_by_vector(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """벡터 기반 검색을 수행합니다."""
        try:
            response = self.es_client.search(
                index=self.index_name,
                body={
                    "query": {
                        "knn": {
                            "embedding": {
                                "vector": query_vector,
                                "k": top_k
                            }
                        }
                    },
                    "size": top_k,
                    "_source": ["content", "title", "source", "page_id"]
                }
            )
            
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    'score': hit['_score'],
                    'content': hit['_source']['content'],
                    'title': hit['_source']['title'],
                    'source': hit['_source']['source'],
                    'page_id': hit['_source']['page_id']
                })
            
            return results
            
        except Exception as e:
            print(f"❌ 벡터 검색 실패: {e}")
            return []
    
    def hybrid_search(self, query: str, query_vector: List[float], top_k: int = 5, 
                     text_weight: float = 0.3, vector_weight: float = 0.7) -> List[Dict[str, Any]]:
        """텍스트와 벡터를 결합한 하이브리드 검색을 수행합니다."""
        try:
            response = self.es_client.search(
                index=self.index_name,
                body={
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["content^2", "title"],
                                        "type": "best_fields",
                                        "fuzziness": "AUTO"
                                    }
                                },
                                {
                                    "knn": {
                                        "embedding": {
                                            "vector": query_vector,
                                            "k": top_k
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "size": top_k,
                    "_source": ["content", "title", "source", "page_id"]
                }
            )
            
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    'score': hit['_score'],
                    'content': hit['_source']['content'],
                    'title': hit['_source']['title'],
                    'source': hit['_source']['source'],
                    'page_id': hit['_source']['page_id']
                })
            
            return results
            
        except Exception as e:
            print(f"❌ 하이브리드 검색 실패: {e}")
            return []

# 사용 예시
if __name__ == "__main__":
    # FAISS에서 Elasticsearch로 변환
    converter = FAISSToElasticsearchConverter("notion_faiss_index")
    
    # 변환 실행
    converter.convert_to_elasticsearch()
    
    # 검색 테스트
    print("\n🔍 텍스트 검색 테스트:")
    results = converter.search_by_text("YBIGTA", top_k=3)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} (점수: {result['score']:.2f})")
        print(f"   내용: {result['content'][:100]}...")
        print()
    
    # 벡터 검색 테스트 (예시 벡터)
    print("🔍 벡터 검색 테스트:")
    example_vector = [0.1] * 4096  # 예시 벡터
    results = converter.search_by_vector(example_vector, top_k=3)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} (점수: {result['score']:.2f})")
        print(f"   내용: {result['content'][:100]}...")
        print() 